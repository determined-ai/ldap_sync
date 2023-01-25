#
# User syncronization LDAP -> SCIM
#

from libs import common as c
from libs import scim_helper as sh

def get_scim_users():
    """ Get existing SCIM users on the platform 
    """
    c.current_scim_users = {}  # reset

    _st = c.start_time()

    resp = sh.get_scim_users()

    c.logger.debug("Execution time %s" % c.stop_time(_st, to_str=True))

    return resp

def compare_scim_users():
    """ Compare current SCIM users on the platform with the LDAP's ones assignging accordingly the operation: add, change, activate, deactivate, delete
    """

    c.scim_users_ops = {'add': [],
                        'update': [],
                        'delete': []
    } # reset

    # seach scim_users (LDAP users converted to SCIM struct) in curr_scim_users to identify updates
    # or new users if not in curr_scim_users
    for user in c.scim_users:  
        # match by userName
        curr_user_matching = next(filter(lambda d: d.get('userName') == user['userName'], c.curr_scim_users), None)

        if curr_user_matching is not None:
            # exists and it is different -> update
            user['id'] = curr_user_matching['id']  # complete the id with the id on the platform
   
            # compare the user on the platform [curr_user_matching] with the one from LDAP [scim_users/user]
            # verifing that each key in [scim_users/user] field is == in [curr_user_matching]
            changed = False
            for k,e in user.items():
                # key don't exists or the value is not matching -> changed / stop
                # new LDAP fields non present in SCIM API returned user's fields are not considered for comparison
                if k in curr_user_matching and e != curr_user_matching[k]:      
                    changed = True
                    break

            if changed:  
                # update
                c.scim_users_ops['update'].append(user)
        else:
            # does not exist -> add
            # if an LDAP user change userName is managed as new user
            c.scim_users_ops['add'].append(user)

    # search curr_scim_users users already on the platform that are not in the scim_users (from LDAP) -> delete
    for user in c.curr_scim_users:
        # match by userName 
        scim_user_matching = next(filter(lambda d: d.get('userName') == user['userName'], c.scim_users), None)

        if scim_user_matching is None and user['active']:
            # if a current user does not exist in scim_users -> deleted
            c.scim_users_ops['delete'].append({ 
                                        'id': user['id'], 
                                        'userName': user['userName']
                                        })

    c.logger.info(f"New users: {len(c.scim_users_ops['add'])} - Users to update: {len(c.scim_users_ops['update'])} - Users to delete: {len(c.scim_users_ops['delete'])}")
    c.logger.info(f"Active Users (LDAP): {len(c.scim_users)} - Total Users (SCIM): {len(c.curr_scim_users)}")


def send_scim_update():
    """ For each user execute on the SCIM API interfacec the assigned operation: add, update, delete
    """
    
    # delete / de-activate users
    for user in c.scim_users_ops['delete']:
        if c.user_plugin is not None:
            c.user_plugin.before_send_user(user, op='delete')
        
        c.logger.debug("Delete user: %s (id: %s)" % (user['userName'], user['id']))
        sh.exec_scim_user_api_req(user, op='delete')

        if c.user_plugin is not None:
            c.user_plugin.after_send_user(user, op='delete')

    # update users
    for user in c.scim_users_ops['update']:
        if c.user_plugin is not None:
            c.user_plugin.before_send_user(user, op='update')
        
        c.logger.debug("Update user: %s (id: %s)" % (user['userName'], user['id']))
        sh.exec_scim_user_api_req(user, op='update')

        if c.user_plugin is not None:
            c.user_plugin.after_send_user(user, op='update')

    # add users
    for user in c.scim_users_ops['add']:
        if c.user_plugin is not None:
            c.user_plugin.before_send_user(user, op='add')
        
        c.logger.debug("Add user: %s" % user['userName'])
        sh.exec_scim_user_api_req(user, op='add')

        if c.user_plugin is not None:
            c.user_plugin.after_send_user(user, op='add')
    

def main_loop():
    """ Main LDAP syncronization function get users from LDAP and sends to SCIM
        deleting, changing, and creating users
        
        It also invokes plugin before/after functions. 
    """

    ldap_ok = c.ldap_plugin.ldap_get_users()

    if ldap_ok:
        # map the LDAP user fields on the MLDE SCIM fileds
        c.ldap_plugin.ldap_to_scim_mapping()
        # get the users list form the platform using SCIM API
        resp = get_scim_users()
        scim_ok = resp['http_status'] in [200,201,202]

        if scim_ok \
            and c.curr_scim_users is not None and len(c.scim_users) > 0:

            # for each user in LADP derived user list define what to do on the SCIM API
            compare_scim_users()
            
            # then execute the changes on the platform user list
            if c.user_plugin is not None:
                c.user_plugin.before_send_all_users()
            
            send_scim_update()
            
            if c.user_plugin is not None:
                c.user_plugin.after_send_all_users()
