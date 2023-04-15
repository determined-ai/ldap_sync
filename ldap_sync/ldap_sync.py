#
# LDAP SYNC main file
#

import sys
import time
import argparse

from libs import common as c
from libs import sync_process as sp

VERSION = '1.1'

# define main 
def main():
    """ Main - Get config, initalize logger, signals hd, and plugins, then pass control to the loop.
        If sync_freq = 0 execute one-shot and exit.
    """
    try:
        # get parameters
        
        parser = argparse.ArgumentParser()
        parser.add_argument('-c', '--config', dest='config_file_path', type=str, help='Configuration YAML file path')
        args = parser.parse_args()

        # initialize the common variables and perform the start-up checks (if negative exit)
        c.init(args.config_file_path, VERSION)  

        # LDAP query loop 
        while True:
            c.logger.info("LDAP Sync process execution start")

            _st =c.start_time()

            sp.main_loop()
                    
            c.logger.debug("Execution time %s" % c.stop_time(_st, to_str=True))

            if 'sync_freq' in c.ldap_config and c.ldap_config['sync_freq'] > 0:
                # wait 
                c.logger.info("LDAP Sync process execution end - waiting %sS" % c.ldap_config['sync_freq'] )
                time.sleep(c.ldap_config['sync_freq'])  # in seconds
            else:
                # one-shot
                c.logger.info("LDAP Sync process execution end - exit")
                sys.exit(0) # exit with no errors

    except Exception as e:
        if str(e) == "SIGINT":
            c.logger.info("SIGINT received - exit")
            sys.exit(128+2) # SIGINT 2
        elif str(e) == "SIGTERM":
            c.logger.info("SIGTERM received - exit")
            sys.exit(128+15) # SIGTERM 15
        else:
            c.logger.error("Exception: %s - exit" % e)
            sys.exit(1) # General error


# start
if __name__ == '__main__':
    main()
    