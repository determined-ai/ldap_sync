#
# LDAP plugin template 
#

import codecs
import uuid

# ref global logger and config
from libs import common as c
from libs import ldap_plugin_common as lpc

def init(*args, **kwargs):
    c.logger.debug("%s %s" % (args, kwargs))

# main function (for testing purposes not currently used)
def main(*args, **kwargs):
    c.logger.debug("%s %s" % (args, kwargs))

def ldap_get_users():
    # current call: ldap_get_users():
    c.logger.debug()

def ldap_user_handler(*args, **kwargs):
    # current call: ldap_user_handler(entry):
    c.logger.debug("%s %s" % (args, kwargs))

def ldap_to_scim_mapping(*args, **kwargs):
    # current call: ldap_to_scim_mapping() 
    c.logger.debug("%s %s" % (args, kwargs))
