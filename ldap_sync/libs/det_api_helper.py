#
# DET API helper module
# Determined API wrapper - User management APIs
#

import requests
import json

from libs import common as c

token = None

def api_call(api, method='GET', payload={}, bearer=None):

    if 'url' in c.det_config:
        url = c.det_config['url']
    else:
        c.logger.error("No Det APIs endpoint URL provided")
        return None

    if bearer is None:
        headers = {
            'Content-Type': 'application/json'
        }
    else:
        headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer '+bearer
        }
        
    try:
        if method.upper() == 'GET':
            #in api if GET also set eventual parameters
            resp = requests.get(url+api , 
                                 headers=headers)

        elif method.upper() == 'POST':
            resp = requests.post(url+api , 
                                    headers=headers,
                                    json=payload)

        elif method.upper() == 'PUT':
            resp = requests.put(url+api , 
                                    headers=headers,
                                    json=payload)
        else:
            # TODO implement other methods
            resp = requests.post(url+api , 
                                    headers=headers,
                                    json=payload)
            
    except requests.exceptions.Timeout:
        # Maybe set up for a retry, or continue in a retry loop
        c.logger.error(f"API call: {api} - Error: Timeout")
        return {'http_status': None, 'response': {}} 
    except requests.exceptions.TooManyRedirects:
            # Tell the user their URL was bad and try a different one
        c.logger.error(f"API call: {api} - Error: Too Many Redirects")
        return {'http_status': None, 'response': {}} 
    except requests.exceptions.RequestException as e:
        c.logger.error(f"API call: {api} - Error: {e}")
        return {'http_status': None, 'response': {}} 


    # Manage REST response
    if resp.status_code in [200,201,202]:   # http ok, created, accepted
        content = json.loads(resp.text)
        c.logger.debug(f"API call: {api} - HTTP ok - status: {resp.status_code}")
        return {'http_status': resp.status_code, 'response': content}
        
    else:
        c.curr_local_users = [] # reset
        c.logger.error(f"API call: {api} - HTTP error - status: {resp.status_code}")
        return {'http_status': resp.status_code, 'response': {}}


def login():
    global token

    if token is not None:    # if an existing connection is open close it
        logout()

    #curl -X POST -s -d '{"username": "admin", "password": "Admin123"}' "${DET_MASTER}/api/v1/auth/login" | jq -r .token

    if 'auth' in c.det_config  \
        and 'username' in c.det_config['auth'] \
        and 'password' in c.det_config['auth']:

        payload = {
            "username": c.det_config['auth']['username'],
            "password": c.det_config['auth']['password'],
            #"isHashed": True
        }

        res = api_call('/api/v1/auth/login', 'POST', payload)
        
        if res['http_status'] == 200 and 'token' in res['response']:
            c.logger.debug("Det API login executed")
            token = res['response']['token']
            return True
        else:
            c.logger.error(f"Det API login error")
            token = None
            return False

    else:
        c.logger.error('Det APIs mandatory connection info are omitted')
        return False

def logout():
    global token

    if token is not None:
        res = api_call('/api/v1/auth/logout', 'POST', bearer=token)
        
        if res['http_status'] == 200:
            token = None
        else:
            token = None    #reset if in error

        return True
    
    else:
        return True

def get_users():
    # curl -X GET -H 'accept: application/json' -H "Authorization: Bearer ${TOKEN}" -H "Content-Type: application/json" "${DET_MASTER}/api/v1/users"
    
    users_byid = {}
    users_byname = {}

    if token is not None:

        res = api_call('/api/v1/users?limit=0', 'GET', bearer=token)

        if res['http_status'] == 200 and 'users' in res['response']:
            for user in res['response']['users']:
                users_byid[user['id']] = user
                users_byname[user['username']] = user

    else:
        c.logger.error('Det APIs token is not available')
    
    return users_byid, users_byname

def get_groups():
    # curl -X POST -s -H 'accept: application/json' -H "Authorization: Bearer ${TOKEN}" -H "Content-Type: application/json" -d '{"limit": -1}' "${DET_MASTER}/api/v1/groups/search" 

    groups_byid = {}
    groups_byname = {}

    if token is not None:

        payload = {
        #     "userId": user_id,
        #     #"name": None,
        #     "offset": 0,
             "limit": -1
        }

        res = api_call('/api/v1/groups/search', 'POST', payload=payload,  bearer=token)

        if res['http_status'] == 200 and 'groups' in res['response']:

            for group in res['response']['groups']:
                groups_byid[group['group']['groupId']] = group['group']
                groups_byname[group['group']['name']] = group['group']
    else:
        c.logger.error('Det APIs token is not available')

    return groups_byid, groups_byname

def get_group_users_byid(group_id):
    #curl -X GET -s -H 'accept: application/json' -H "Authorization: Bearer ${TOKEN}" "${DET_MASTER}/api/v1/groups/9?orderBy=ORDER_BY_DESC&limit=-1" 

    users_byid = {}

    if token is not None:

        res = api_call(f'/api/v1/groups/{group_id}?orderBy=ORDER_BY_DESC&limit=-1', 'GET', bearer=token)

        if res['http_status'] == 200 and 'group' in res['response'] \
            and 'users' in res['response']['group']:

            for user in res['response']['group']['users']:
                users_byid[user['id']] = user
    else:
        c.logger.error('Det APIs token is not available')

    return users_byid


def group_add_rm_users(group_id, add_user_ids=[], rm_user_ids=[]):
    # curl -X POST -s -H 'accept: application/json' -H "Authorization: Bearer ${TOKEN}" -H "Content-Type: application/json" -d '{"addUsers": [3], "removeUsers": []}' -X PUT "${DET_MASTER}/api/v1/groups/9" 

    if token is not None:

        payload = {
            #"groupId": 0,
            #"name": "string",  
            "addUsers": add_user_ids,
            "removeUsers": rm_user_ids
        }

        res = api_call(f'/api/v1/groups/{group_id}', 'PUT', payload=payload,  bearer=token)

        if res['http_status'] == 200 and 'group' in res['response'] \
            and 'users' in res['response']['group']:

            users = res['response']['group']['users']
        else:
            users = []    #reset if in error

        return users
    else:
        c.logger.error('Det APIs token is not available')
        return []
