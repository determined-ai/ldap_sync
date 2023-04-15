#
# Common globals
#

import os
import sys
import signal 
import logging
import time
import yaml 
import re

from datetime import datetime

from libs import plugin as plg

# define common global consts
LOGGER_NAME = 'ldap_sync'
CONFIG_FILE = "config.yaml"  # path relative to the main file
PLUGIN_LIB = "plugins"

# common global vars definintion
# these vars are global to permit to every module and plugin to access it

logger = logging.getLogger(LOGGER_NAME)

# configuration
config = {}
user_management_api = 'scim'   # scim|det platform api used to manage users
ldap_config = {}        # ldap branch
ldap_config_auth = {}   # ldap auth branch
ldap_config_users = {}  # ldap users branch
scim_config = {}        # scim_api branch SCIM APIs when user_management_api = 'scim'
det_config = {}         # det_api branch Determined APIs when user_management_api = 'det'

# plug in
ldap_plugin = None      # plugin vendor-dependent for LDAP entries processing and maping onto SCIM users
user_plugin = None      # (optional) plugin to exectute operations before and after users update on the plaform 
curr_dir = ""           # main file current directory

# user list
ldap_users = []         # raw users data retrieved from LDAP
local_users = []        # user list coming from LDAP to be sent to the Determined platform. It contains users converted from LDAP to SCIM struct; 
                        # and it is also used by the Determined APIs functionality
curr_local_users = []   # user list coming from the Determined platform, by SCIM or by DET APIs

# SCIM user list with operations to be executed on the SCIM API or Determined API interfaces
local_users_ops = { 'add': [],
                    'update': [],
                    'delete': []
} 

# common general purpose functions 

def start_time():
    """ Starts the time measurement
        Usage:
            _st = start_time()
            duration_sec = stop_timer(_st)

        Returns:
            current time in mS
    """
    return time.time()

def stop_time(start, to_str=False):
    """ Stops the time measurement
        Usage:
            _st = start_time()
            duration_sec = stop_timer(_st)
        Args:
            start: start time (from start_time())
            to_str: (optional, default: False) if true returns the result as string + "S"
        Returns:
            lapsed time time seconds (rounded 3 digits)
    """
    ts = round((time.time() - start), 3) # in seconds

    if to_str:
        return '%sS' % str(ts)
    else:
        return ts

# define signal handelers

def _sigterm(signal, frame):
    """ Standard signal SIGTERM handler (private)
        Termination signal

        Rises:
            Exception("SIGTERM")
    """
    
    # release resources here (if needed)
    raise Exception("SIGTERM")

def _sigint(signal, frame):
    """ Standard signal SIGINT handler (private)
        Ctrl-C signal
        
        Rises:
            Exception("SIGINT")
    """
    # release resources here (if needed)
    raise Exception("SIGINT")

class ObjectGUID:
    _guid = ""
    def __init__(self, value):
        self._guid = value
        return value

    def to_str(self):
        return str(self._guid)

# common initialization
def init(config_file_path=None, version=''):
    """ common module init 
        
        ATTENTION: THIS init() IS TO BE CALLED ONLY IN THE MAIN FUNCTION

        Args:
            config_file_path: (optional str) full pathn of the config file, 
            if not provided config file path: current dir + '/' + CONFIG_FILE 

        Raises:
            signal and file exceptions to be managed
    """
    
    global logger, config, ldap_plugin, user_plugin, curr_dir, \
           ldap_config, ldap_config_auth, ldap_config_users, \
           scim_config, det_config, user_management_api

    # set current dir
    curr_dir = os.path.dirname(os.path.abspath(__file__))
    curr_dir = os.path.abspath(os.path.join(curr_dir, os.pardir)) # ".." common module is libs dir

    # logger setup
    logger = logging.getLogger(LOGGER_NAME)
    logger.setLevel( logging.INFO ) # default logger level: INFO
    # standard format
    # logFormatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    # verbose readable format
    logFormatter = logging.Formatter("%(asctime)s %(levelname)-8s %(filename)-20s:%(funcName)-20s %(message)s")
    
    # MLDE format
    # logFormatter = logging.Formatter("%(levelname)-5s[%(asctime)s] %(message)s", 
    #                                  datefmt = '%Y-%m-%dT%H:%M:%S%Z')

    consoleHandler = logging.StreamHandler(sys.stdout) # set streamhandler to stdout
    consoleHandler.setFormatter(logFormatter)
    logger.addHandler(consoleHandler)

    # assign signal handlers
    signal.signal(signal.SIGTERM, _sigterm)  
    signal.signal(signal.SIGINT, _sigint)

    logger.info(f"HPE MLDE - LDAP Sync ver. {version} (c) 2023 Hewlett Packard Enterprise, All rights reserved.")

    if config_file_path is not None and isinstance(config_file_path, str) and len(config_file_path) > 0:
        if os.path.isabs(config_file_path):
            # absolute path
            config_filename = config_file_path
        else:
            # relative path
            config_filename = os.path.join(curr_dir, config_file_path) #  common module is libs dir
    else:
        config_filename = os.path.join(curr_dir, CONFIG_FILE)

    # read configuration
    try:
        logger.info("Loading configuration [%s]" % config_filename)
        
        # Setup the !ENV tag processing 
        # to manage environment variables 

        def _get_node_env_value(loader, node):
            """
            (priv) Gets the environment variable value from the node's value.

            Args:
                loader: the yaml loader
                node: the current node in the yaml
            
            Returns:
                The environment variable value.
                If the environment variable is not defined, the value is the variable name.
            """
            env_var = loader.construct_scalar(node)
            return os.environ.get(env_var, env_var)
        
        tag = "!ENV" # yaml tag to intercept
        pattern = re.compile('.*?(\w+).*?')  # patter to extract the tag content (a string)
        loader = yaml.SafeLoader
        loader.add_implicit_resolver(tag, pattern, None)
        loader.add_constructor(tag, _get_node_env_value)

        # load configuration
        with open(config_filename) as fd:
            config = yaml.load(fd, Loader=loader)

    except Exception as e:
        logger.error("Error loading configuration - error: %s" % str(e))
        sys.exit(1) # General error

    # set logger level if provided in configuration
    if 'log' in config and 'level' in config['log']:
        logger.setLevel( getattr(logging, config['log']['level'].upper()) ) # set logger level
    else:
        logger.setLevel( getattr(logging, "INFO") ) # set logger level to INFO default
    
    logger.debug("Configuration: %s" % config)

    # get main configuration branches

    if 'ldap' in config:
        ldap_config = config['ldap']

        if 'auth' in ldap_config and 'users' in ldap_config:
            ldap_config_auth  = ldap_config['auth']
            ldap_config_users = ldap_config['users']
        else:
            logger.error("Config does not contain [ldap.auth or ldap.users] key - exit")
            sys.exit(1) # General error
    else:
        logger.error("Config does not contain [ldap] key - exit")
        sys.exit(1) # General error

    if 'user_management_api' in config:
        api_type = config['user_management_api']
        
        if api_type.lower() == 'scim':
            user_management_api = 'scim'
            logger.error("SCIM user management API enabled")

            if 'scim_api' in config:
                scim_config = config['scim_api']
            else:
                logger.error("Config does not contain [scim_api] key - exit")
                sys.exit(1) # General error
        elif api_type.lower() == 'det':
            user_management_api = 'det'
            logger.error("Determined user management API enabled")

            if 'det_api' in config:
                det_config = config['det_api']
            else:
                logger.error("Config does not contain [det_api] key - exit")
                sys.exit(1) # General error
        else:
            logger.error(f"Unhandled API type [{api_type}] - exit")
            sys.exit(1) # General error
    else:
        logger.error("Config does not contain [users_management_api] key - exit")
        sys.exit(1) # General error

    # plugins loader
    if 'ldap_plugin' in ldap_config:
        logger.info("LDAP plugin [%s] enabled" % ldap_config['ldap_plugin'])
        ldap_plugin = plg.load(ldap_config['ldap_plugin'], init=True)

        if ldap_plugin is None or ldap_plugin == False:
            logger.error("Cannot load LDAP plugin - exit") # LDAP plugin must be ready
            sys.exit(1) # General error
    else: 
        logger.error("LDAP plugin (ldap_plugin key) not defined in configuration - exit")
        sys.exit(1) # General error

    if 'user_plugin' in ldap_config:
        if ldap_config['user_plugin'] is None:
            logger.info("User plugin disabled")
        else:
            logger.info("User plugin [%s] enabled" % ldap_config['user_plugin'])
            user_plugin = plg.load(ldap_config['user_plugin'], init=True)

            if user_plugin is None:
                logger.error("Cannot load defined User plugin - exit") # User plugin, if defined, must be ready
                sys.exit(1) # General error
    else:
        logger.info("User plugin disabled")