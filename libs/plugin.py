#
# Simple plugin managment module
#

import importlib
from libs import common as c

def load(plugin_name, init=True):
    """ Loads a plugin and initialize it

        Args:
            plugin_name: name of the plugin module in plugins directory
            init: (defult True) initalize the plugin after load

        Returns:
            module ref or None if error

        Raises:
            N/A
    """

    try:
        # curr_dir = os.path.dirname(os.path.abspath(__file__))
        # plugin_dir = os.path.join(curr_dir, PLUGIN_DIRECTORY)
        mod = importlib.import_module(c.PLUGIN_LIB+"."+plugin_name)
        c.logger.info("Plugin [%s] loaded" % (plugin_name))

        if init:
            c.logger.debug("Initializing plugin [%s]" % (plugin_name))
            mod.init()

        return mod

    except Exception as e:
        c.logger.error("Plugin [%s] not loaded - error: %s" % (plugin_name, e))
        return None

# example of call
# def call_plugin(name, *args, **kwargs):
#    plugin = load_plugin(name)
#    plugin.main(*args, **kwargs)
#
# call_plugin("example", 1234)