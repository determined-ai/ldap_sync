#
# User syncronization LDAP -> SCIM or DET
#

from libs import common as c
from libs import scim_helper as sh
#from libs import det_helper as dh

def get_scim_users():
    """ Get existing SCIM users on the platform 
    """
    c.curr_local_users = {}  # reset

    _st = c.start_time()

    resp = sh.get_scim_users()

    c.logger.debug("Execution time %s" % c.stop_time(_st, to_str=True))

    return resp

def compare_scim_users():
    """ Compare current SCIM users on the platform with the LDAP's ones assignging accordingly the operation: add, change, activate, deactivate, delete
    """

    c.local_users_ops = {'add': [],
                         'update': [],
                         'delete': []
    } # reset

    # seach local_users (user coming from LDAP) in curr_local_users to identify updates
    # or new users if not in curr_local_users
    for user in c.local_users:  
        # match by userName
        curr_user_matching = next(filter(lambda d: d.get('userName') == user['userName'], c.curr_local_users), None)

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
                c.local_users_ops['update'].append(user)
        else:
            # does not exist -> add
            # if an LDAP user change userName is managed as new user
            c.local_users_ops['add'].append(user)

    # search curr_local_users = users already on the platform, that are NOT in the local_users (coming from LDAP) -> delete
    for user in c.curr_local_users:
        # match by userName 
        local_user_matching = next(filter(lambda d: d.get('userName') == user['userName'], c.local_users), None)

        if local_user_matching is None and user['active']:
            # if a current user does not exist in local_users -> deleted
            c.local_users_ops['delete'].append({ 
                                        'id': user['id'], 
                                        'userName': user['userName']
                                        })

    c.logger.info(f"New users: {len(c.local_users_ops['add'])} - Users to update: {len(c.local_users_ops['update'])} - Users to delete: {len(c.local_users_ops['delete'])}")
    c.logger.info(f"Active Users (LDAP): {len(c.local_users)} - Total Users (SCIM): {len(c.curr_local_users)}")

def send_scim_update():
    """ For each user execute on the SCIM API interface the assigned operation: add, update, delete
    """
    
    # delete / de-activate users
    for user in c.local_users_ops['delete']:
        if c.user_plugin is not None:
            c.user_plugin.before_send_user(user, op='delete')
        
        c.logger.debug("Delete user: %s (id: %s)" % (user['userName'], user['id']))
        sh.exec_scim_user_api_req(user, op='delete')

        if c.user_plugin is not None:
            c.user_plugin.after_send_user(user, op='delete')

    # update users
    for user in c.local_users_ops['update']:
        if c.user_plugin is not None:
            c.user_plugin.before_send_user(user, op='update')
        
        c.logger.debug("Update user: %s (id: %s)" % (user['userName'], user['id']))
        sh.exec_scim_user_api_req(user, op='update')

        if c.user_plugin is not None:
            c.user_plugin.after_send_user(user, op='update')

    # add users
    for user in c.local_users_ops['add']:
        if c.user_plugin is not None:
            c.user_plugin.before_send_user(user, op='add')
        
        c.logger.debug("Add user: %s" % user['userName'])
        sh.exec_scim_user_api_req(user, op='add')

        if c.user_plugin is not None:
            c.user_plugin.after_send_user(user, op='add')

def get_det_users():
    """ Get existing user on the platform with DET APIs (Standard users)
    """
    c.curr_local_users = {}  # reset

    try:
        _st = c.start_time()
        # det_cli.login( master=c.config['det_sync']['url'],
        #             user=c.config['det_sync']['auth']['username'],
        #             password=c.config['det_sync']['auth']['password'],
        #             cert_path=None,
        #             cert_name=None,
        #             noverify= False)

        # user_list = det_cli.list_users()

        # # map users
        # for user in user_list:
        #     c.curr_local_users.append({
        #         "active": user.active,
        #         "admin": user.admin,
        #         "agent_gid": user.agent_gid,
        #         "agent_group": user.agent_group,
        #         "agent_uid": user.agent_uid,
        #         "agent_user": user.agent_user,
        #         "display_name": user.display_name,
        #         "user_id": user.user_id,
        #         "username": user.username,
        #     })

        c.logger.debug("Execution time %s" % c.stop_time(_st, to_str=True))

        return True

    except Exception as e:
        c.logger.error(f"Error reading Users form DET APIs - error: {e}")
        return False

def compare_det_users():
    """ Compare current DET API users (only standard user, not admin) that on the platform 
        with the LDAP's ones assignging accordingly the operation: add, change, activate, deactivate, delete
    """
    return True

def send_det_update():
    """ For each user execute on the DET API interface the assigned operation: add, update, delete
    """
    return True



def main_loop():
    """ Main LDAP syncronization function get users from LDAP and sends to SCIM
        deleting, changing, and creating users
        
        It also invokes plugin before/after functions. 
    """

    ldap_ok = c.ldap_plugin.ldap_get_users()

    if ldap_ok:
        if c.user_management_api == 'det':
            # DET APIs
            
            # map the LDAP user fields on the MLDE DET fileds
            c.ldap_plugin.ldap_to_det_mapping()
            #TODO c.ldap_plugin.ldap_to_det_mapping()

            # get the users list form the platform using DET API
            det_api_ok = get_det_users()
             
            if det_api_ok \
                and c.curr_local_users is not None and len(c.local_users) > 0:
                # for each user in LADP derived user list define what to do on the DET API
                compare_det_users()
                    
                # then execute the changes on the platform user list
                if c.user_plugin is not None:
                    c.user_plugin.before_send_all_users()
                
                send_det_update()
                
                if c.user_plugin is not None:
                    c.user_plugin.after_send_all_users()
        else:
            # SCIM APIs

            # map the LDAP user fields on the MLDE SCIM fileds
            c.ldap_plugin.ldap_to_scim_mapping()

            # get the users list form the platform using SCIM API
            resp = get_scim_users()
            scim_ok = resp['http_status'] in [200,201,202]

            if scim_ok \
                and c.curr_local_users is not None and len(c.local_users) > 0:

                # for each user in LADP derived user list define what to do on the SCIM API
                compare_scim_users()
                    
                # then execute the changes on the platform user list
                if c.user_plugin is not None:
                    c.user_plugin.before_send_all_users()
                
                send_scim_update()
                
                if c.user_plugin is not None:
                    c.user_plugin.after_send_all_users()
