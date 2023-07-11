#
# User synchronization process LDAP -> SCIM 
#

import re

from libs import common as c
from libs import scim_helper as sh
from libs import det_api_helper as det
from libs import ldap_plugin_common as lpc

def get_scim_users():
    """ Get existing SCIM users on the platform 
    """
    c.curr_local_users = {}  # reset

    _st = c.start_time()

    resp = sh.get_scim_users()

    c.logger.debug("Execution time %s" % c.stop_time(_st, to_str=True))

    return resp

def compare_scim_users():
    """ Compare current SCIM users on the platform with the LDAP's ones assigning accordingly the operation: add, change, activate, deactivate, delete
    """

    c.local_users_ops = {'add': [],
                         'update': [],
                         'delete': []
    } # reset

    # search local_users (user coming from LDAP) in curr_local_users to identify updates
    # or new users if not in curr_local_users
    for user in c.local_users:  
        # match by userName
        curr_user_matching = next(filter(lambda d: d.get('userName') == user['userName'], c.curr_local_users), None)

        if curr_user_matching is not None:
            # exists and it is different -> update
            user['id'] = curr_user_matching['id']  # complete the id with the id on the platform
   
            # compare the user on the platform [curr_user_matching] with the one from LDAP [scim_users/user]
            # verifying that each key in [scim_users/user] field is == in [curr_user_matching]
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
        if c.custom_plugin is not None:
            c.custom_plugin.before_send_user(user, op='delete')
        
        c.logger.debug("Delete user: %s (id: %s)" % (user['userName'], user['id']))
        sh.exec_scim_user_api_req(user, op='delete')

        if c.custom_plugin is not None:
            c.custom_plugin.after_send_user(user, op='delete')

    # update users
    for user in c.local_users_ops['update']:
        if c.custom_plugin is not None:
            c.custom_plugin.before_send_user(user, op='update')
        
        c.logger.debug("Update user: %s (id: %s)" % (user['userName'], user['id']))
        sh.exec_scim_user_api_req(user, op='update')

        if c.custom_plugin is not None:
            c.custom_plugin.after_send_user(user, op='update')

    # add users
    for user in c.local_users_ops['add']:
        if c.custom_plugin is not None:
            c.custom_plugin.before_send_user(user, op='add')
        
        c.logger.debug("Add user: %s" % user['userName'])
        sh.exec_scim_user_api_req(user, op='add')

        if c.custom_plugin is not None:
            c.custom_plugin.after_send_user(user, op='add')

def auto_assign_mlde_groups():
    """ For each user checks if is part of an LDAP group and if this group exists on the platform automatically assign/de-assign the user to the group
    """
  
    # login
    if det.login():      
    
        _st = c.start_time()

        # get the list of MLDE users maps accessible by name and id
        det_users_byid, det_users_byname = det.get_users()

        # get the list of MLDE groups maps accessible by name and id
        det_groups_byid, det_groups_byname = det.get_groups()


        # get the list of MLDE groups and related users 
        det_groups_users_bygroup_id = {}
        for group_id, _ in det_groups_byid.items():
            grp_users_byid = det.get_group_users_byid(group_id)
            det_groups_users_bygroup_id[group_id] = grp_users_byid
            # sleep 100-200ms to not flood the API ???
            
        # get group name filter string from det_api.auto_assign_mlde_groups config
        if 'group_string_filter' in c.det_config['auto_assign_mlde_groups']['group_string_filter']:
            group_search_re = c.det_config['auto_assign_mlde_groups']['group_string_filter']
        else:
            group_search_re = '^CN=(.+?)\,'   # match the first "CN=" up to the first ','

        c.logger.debug(f"Group name filtering regex: {group_search_re}")

        det_group_assigned_user_ids = {}
        det_group_add_user_ids = {}
        det_group_rm_user_ids = {}

        c.logger.debug(f"Users automatic assignment to group/s: enabled")

        # ADD (Assign)
        # scan can the user that are on LDAP (converted to SIM struct)
        for user in c.local_users:
            # local_users user list contains mapped/converted users from LDAP to SCIM struct
            user_name = user['userName']
            member_of = user['memberOf']

            # gets the user id on the platform 
            if user_name in det_users_byname:
                user = det_users_byname[user_name]   # found
                user_id = user['id']   # found

                # safety array conversion 
                # in case the group DN is not passed or it is passed as a string (by LDAP)
                if member_of is None:
                    member_of =[]
                if type(member_of) is str:
                    member_of = [member_of]
                
                c.logger.debug(f"User name: {user_name} - User id: {user_id}")
                c.logger.debug(f"User member of group/s: {member_of}")

                # ADD
                # scan groups the user is member of --> add 
                for m_group in member_of:

                    # extracts the group name
                    group_name = ""
                    m = re.search(group_search_re, str(m_group) )
                    if m:
                        # found
                        group_name = m.group(1)

                        if group_name in det_groups_byname:
                            group = det_groups_byname[group_name]   # found
                            group_id = group['groupId']

                            if group_id in det_groups_users_bygroup_id:
                                grp_users = det_groups_users_bygroup_id[group_id]

                                if user_id in grp_users:
                                    # found 
                                    c.logger.debug(f"User {user_id} is already in group {group_id} ")
                                else:
                                    # not found --> add
                                    c.logger.debug(f"User {user_id} to be added to group {group_id} ")
                                    if group_id not in det_group_add_user_ids:
                                        det_group_add_user_ids[group_id] = list()   #init list

                                    det_group_add_user_ids[group_id].append(user_id)

                                # update assigned users (both existing and to be added)
                                if group_id not in det_group_assigned_user_ids:
                                    det_group_assigned_user_ids[group_id] = list()   #init list

                                det_group_assigned_user_ids[group_id].append(user_id)
                                    
                        else:
                            # group not found on the platform -> skip
                            c.logger.debug(f"On LDAP user {user_id} is assigned to a group {group_name} that is not available - Skip group assignment")
                    else:
                        # group name not found in memberOf
                        c.logger.error(f"No matching group in memberOf field: {str(m_group)} - Skip group assignment")
            else:
                c.logger.error(f"Error - User name: {user_name} has not a matching user id")
        
        c.logger.debug(f"Users assigned to groups: {det_group_assigned_user_ids} ")
        c.logger.debug(f"Users to add to groups: {det_group_add_user_ids} ")

        # add users to groups
        for group_id in det_group_add_user_ids:
            add_user_ids = det_group_add_user_ids[group_id]
            det.group_add_rm_users(group_id, add_user_ids=add_user_ids)


        # REMOVE (De-assign)
        # if enabled scan groups/users, if they are not in the det_group_assigned_user_ids remove the user/s
        if 'auto_assign_mlde_groups' in c.det_config \
            and 'enabled' in c.det_config['auto_assign_mlde_groups'] \
            and c.det_config['auto_assign_mlde_groups']['enabled'] \
            and 'auto_removal_enabled' in c.det_config['auto_assign_mlde_groups'] \
            and c.det_config['auto_assign_mlde_groups']['auto_removal_enabled']:
            
            c.logger.debug(f"Users automatic removal from groups: enabled")

            for assigned_group_id in det_groups_users_bygroup_id:
                for assigned_user_id in det_groups_users_bygroup_id[assigned_group_id]:
                    remote_user = det_groups_users_bygroup_id[assigned_group_id][assigned_user_id]['remote']
                    if assigned_user_id not in det_group_assigned_user_ids[assigned_group_id] and remote_user:
                        # not found any remote user -> remove
                        if assigned_group_id not in det_group_rm_user_ids:
                            det_group_rm_user_ids[assigned_group_id] = list()   #init list

                        det_group_rm_user_ids[assigned_group_id].append(assigned_user_id) 
                        c.logger.debug(f"User {assigned_user_id} is not in group {assigned_group_id} - remove")
                    else:
                        # found -> don't remove
                        if remote_user:
                            c.logger.debug(f"User {assigned_user_id} is in group {assigned_group_id} - remote user - don't remove")
                        else:
                            c.logger.debug(f"User {assigned_user_id} is in group {assigned_group_id} - non-remote user - don't remove")

            c.logger.debug(f"Users to remove from groups: {det_group_rm_user_ids} ")
            
            # remove users from groups
            for group_id in det_group_rm_user_ids:
                rm_user_ids = det_group_rm_user_ids[group_id]
                det.group_add_rm_users(group_id, rm_user_ids=rm_user_ids)
        else:
            c.logger.debug(f"Users automatic removal from groups: disabled")

        # logout
        det.logout()
        c.logger.debug("Execution time %s" % c.stop_time(_st, to_str=True))
        c.logger.debug(80*"*")
        return True
    else:
        # no login
        return False



def main_loop():
    """ Main LDAP synchronization function get users from LDAP and sends to SCIM
        deleting, changing, and creating users
        
        It also invokes plugin before/after functions. 
    """

    ldap_ok = c.ldap_plugin.ldap_get_users()

    if ldap_ok:

        # TODO remove
        # if c.user_management_api == 'det':
        #     # DET APIs
            
        #     # map the LDAP user fields on the MLDE DET fields
        #     c.ldap_plugin.ldap_to_det_mapping()
        #     #TODO c.ldap_plugin.ldap_to_det_mapping()

        #     # get the users list form the platform using DET API
        #     det_api_ok = get_det_users()
             
        #     if det_api_ok \
        #         and c.curr_local_users is not None and len(c.local_users) > 0:
        #         # for each user in LDAP derived user list define what to do on the DET API
        #         compare_det_users()
                    
        #         # then execute the changes on the platform user list
        #         if c.custom_plugin is not None:
        #             c.custom_plugin.before_send_all_users()
                
        #         send_det_update()
                
        #         if c.custom_plugin is not None:
        #             c.custom_plugin.after_send_all_users()
        # else:

        # SCIM APIs

        # map the LDAP user fields on the MLDE SCIM fields
        c.ldap_plugin.ldap_to_scim_mapping()

        # get the users list form the platform using SCIM API
        resp = get_scim_users()
        scim_ok = resp['http_status'] in [200,201,202]

        if scim_ok \
            and c.curr_local_users is not None and len(c.local_users) > 0:

            # for each user in LDAP derived user list define what to do on the SCIM API
            compare_scim_users()
                
            # then execute the changes on the platform user list
            if c.custom_plugin is not None:
                c.custom_plugin.before_send_all_users()
            
            send_scim_update()
            
            if c.custom_plugin is not None:
                c.custom_plugin.after_send_all_users()

        # verify if auto assign of MLDE group is active and execute it
        if 'auto_assign_mlde_groups' in c.det_config \
            and 'enabled' in c.det_config['auto_assign_mlde_groups'] \
            and c.det_config['auto_assign_mlde_groups']['enabled']:
            auto_assign_mlde_groups()

