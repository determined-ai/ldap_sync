#
# Customization plugin template 
#

# ref global logger and config
from libs import common as c
from libs import custom_plugin_common as cpc

def init(*args, **kwargs):
    c.logger.debug("%s %s" % (args, kwargs))

# main function (not currently used)
def main(*args, **kwargs):
    c.logger.debug("%s %s" % (args, kwargs))

# handlers called during user creation

def before_send_all_users(*args, **kwargs):
    c.logger.debug("%s %s" % (args, kwargs))

def before_send_user(*args, **kwargs):
    c.logger.debug("%s %s" % (args, kwargs))

def after_send_user(*args, **kwargs):
    c.logger.debug("%s %s" % (args, kwargs))

def after_send_all_users(*args, **kwargs):
    c.logger.debug("%s %s" % (args, kwargs))
