#
# DET APIs helper testing
#
import argparse

from libs import common as c
from libs import det_api_helper as dh

VERSION='1.0'

def main_test():

    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--config', dest='config_file_path', type=str, help='Configuration YAML file path')
    args = parser.parse_args()

    # initialize the common variables and perform the start-up checks (if negative exit)
    c.init(args.config_file_path, VERSION)  

    # regex to extract the group name from the LDAP group
    import re
    group = 'CN=DetGroup,CN=Users,DC=ds,DC=det-dcellai-win-ldap-srv,DC=c,DC=determined-ai,DC=internal'
    group_search = '^CN=(.+?)\,'
    m = re.search(group_search, group)
    if m:
        found = m.group(1)
        print(f"found: {found}")



    ###########################################
    # Test DET APIs helper

    c.logger.info(80*"=")
    c.logger.info("DET API helper unit test - start")
    
    # Login user
    c.logger.info(80*"-")
    c.logger.info("Login")
    
    res = dh.det_login()
    
    print(res)

   # Get user list
    c.logger.info(80*"-")
    c.logger.info("DET API Get User list")
   
    res = dh.det_get_users()

    print(res)

    users = res['response']['users']       # store users

    c.logger.info(80*"-")
    c.logger.info("DET API Get group/s")
    
    res = dh.det_get_groups()

    print(res)

    c.logger.info(80*"-")
    c.logger.info("DET API Get each user group/s")
   
    
    print(f'user list {users}')

    for u in users:
        if u['active'] == True:
            user_id = int( u['id'] )
            username = u['username']
            print(f"{user_id} - {username}:")
            res = dh.det_get_groups_search(user_id)
            print(res)

    # Logout user
    c.logger.info(80*"-")
    c.logger.info("DET API Logout")
   
    res = dh.det_logout()

    print(res)

if __name__ == "__main__":
    main_test()