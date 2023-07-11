#
# Plug-in infra testing
# LDAP plug-in and helper testing
#

from libs import common as c
from libs import plugin as plg


def main_test():
    c.init()
 
    ###########################################
    # LDAP plugin 

    c.logger.info(80*"=")

    c.logger.info("LDAP Plugin unit test - start")
    _st = c.start_time()

    # testing plugin load call
    c.ldap_plugin = plg.load('ldap_plugin_template', init=False)
    c.logger.info("### Correct output: load-only no init")

    # testing plugin load call
    c.ldap_plugin = plg.load('ldap_plugin_template', init=True)
    c.logger.info("### Correct output: () {}")


    # testing plugin function call
    if c.ldap_plugin is not None: #if loaded exec function
        c.ldap_plugin.main('test', ['test1', 'test2'], a=10)
        c.logger.info("### Correct output: ('test', ['test1', 'test2']) {'a': 10}")

    # get LDAP users - plugin: ms_active_directory
    c.logger.info("Get LDAP Users - test start")
    c.ldap_plugin = plg.load('ms_active_directory', init=True)
    c.ldap_users = [] # reset
    
    # get users calling the ldap plugin ldap_get_users function
    c.logger.info(80*"-")
    c.logger.info("Get LDAP Users - calling the ldap plugin ldap_get_users function")
    resp_ok = c.ldap_plugin.ldap_get_users()

    c.logger.info("Get LDAP Users - calling the ldap_helper function")

    c.logger.info("Get LDAP Users response: %s" % resp_ok)
    c.logger.info("### Correct output: True")


    # get users calling the ldap_helper function
    c.logger.info(80*"-")

    from libs import ldap_helper as lh

    auth_config  = c.config['ldap_sync']['auth']
    users_config = c.config['ldap_sync']['users']
        
    resp_ok = lh.ldap_retrieve_users(   auth_config['url'],
                                auth_config['user'],
                                auth_config['password'],
                                users_config['dn'],
                                users_config['attr'],
                                users_config['filter'],
                                auth_config['tls'], 
                                # handle_entry = c.ldap_plugin.ldap_user_handler
                                )


    c.logger.info("Get LDAP Users response: %s" % resp_ok)
    c.logger.info("### Correct output: True")

    c.logger.info("LDAP Plugin unit test - end")
    c.logger.info("Execution: " + c.stop_time(_st, to_str=True))


    ###########################################
    # USER plugin 

    c.logger.info(80*"=")
    c.logger.info("USER Plugin unit test - start")
    _st = c.start_time()

    # testing plugin load call
    c.user_plugin = plg.load('user_plugin_template', init=False)
    c.logger.info("### Correct output: load-only no init")

    # testing plugin load call
    c.user_plugin = plg.load('user_plugin_template', init=True)
    c.logger.info("### Correct output: () {}")


    # testing plugin function call
    if c.user_plugin is not None: #if loaded exec function
        c.user_plugin.main('test', ['test1', 'test2'], a=10)
        c.logger.info("### Correct output: ('test', ['test1', 'test2']) {'a': 10}")

    c.logger.info("Execution: " + c.stop_time(_st, to_str=True))
    c.logger.info("USER Plugin unit test - end")
    c.logger.info("Execution: " + c.stop_time(_st, to_str=True))

    

if __name__ == "__main__":
    main_test()