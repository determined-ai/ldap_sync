#
# DET API helper module
# Determined API wrapper (user management)
#

import requests
import json

from libs import common as c

det_auth_resp = {}

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
        else:
            # TODO implement other methods
            resp = requests.post(url+api , 
                                    headers=headers,
                                    json=payload)
            
    except requests.exceptions.Timeout:
        # Maybe set up for a retry, or continue in a retry loop
        c.logger.error("Error contacting Det APIs - error: Timeout")
        return {'http_status': None, 'response': {}} 
    except requests.exceptions.TooManyRedirects:
            # Tell the user their URL was bad and try a different one
        c.logger.error("Error contacting Det APIs - error: Too Many Redirects")
        return {'http_status': None, 'response': {}} 
    except requests.exceptions.RequestException as e:
        c.logger.error("Error contacting Det APIs - error: %s", e)
        return {'http_status': None, 'response': {}} 


    # Manage REST response
    if resp.status_code in [200,201,202]:   # http ok, created, accepted
        content = json.loads(resp.text)
        c.logger.debug("HTTP status: %d" % resp.status_code)
        return {'http_status': resp.status_code, 'response': content}
        
    else:
        c.curr_local_users = [] # reset
        c.logger.error("HTTP error - status: %d" % resp.status_code)
        return {'http_status': resp.status_code, 'response': {}}





def det_login():
    global det_auth_resp

    if 'auth' in c.det_config  \
        and 'username' in c.det_config['auth'] \
        and 'password' in c.det_config['auth']:

        payload = {
            "username": c.det_config['auth']['username'],
            "password": c.det_config['auth']['password'],
            "isHashed": True
        }

        res = api_call('/api/v1/auth/login', 'POST', payload)
        
        if res['http_status'] == 200 and 'token' in res['response']:
            c.logger.debug("Det API login executed")
            det_auth_resp = res['response']
        else:
            det_auth_resp ={} # reset

        return res

    else:
        c.logger.error('Det APIs mandatory connection info are omitted')
        return None

def det_logout():
    global det_auth_resp

    if 'token' in det_auth_resp:
        token = det_auth_resp['token']

        res = api_call('/api/v1/auth/logout', 'POST', bearer=token)
        
        if res['http_status'] == 200:
            det_auth_resp = {}
        else:
            det_auth_resp = {}    #reset

        return res
    else:
        c.logger.error('Det APIs token must be provided')
        return {}

def det_get_users():
    if 'token' in det_auth_resp:
        token = det_auth_resp['token']

        res = api_call('/api/v1/users?sortBy=SORT_BY_ACTIVE&orderBy=ORDER_BY_DESC&offset=0&limit=0', 'GET', bearer=token)

        return res
    else:
        c.logger.error('Det APIs token must be provided')
        return {}

def det_add_user():
    ...

def det_update_user():
    ...

def det_set_user_admin_rights():
    ...

def det_remove_user_admin_rights():
    ...

def det_get_groups_search(user_id):
    if 'token' in det_auth_resp:
        token = det_auth_resp['token']


        payload = {}
        # payload = {
        #     "userId": user_id,
        #     #"name": None,
        #     "offset": 0,
        #     "limit": 0
        # }

        res = api_call('/api/v1/groups/search', 'POST', payload=payload,  bearer=token)

        return res
    else:
        c.logger.error('Det APIs token must be provided')
        return {}


def det_get_groups():
    if 'token' in det_auth_resp:
        token = det_auth_resp['token']

        payload = {}

        res = api_call('/api/v1/groups', 'POST', payload=payload,  bearer=token)

        return res
    else:
        c.logger.error('Det APIs token must be provided')
        return {}

def det_add_user_to_group():
    ...

def det_remove_user_from_group():
    ...




























def _get_scim_access_param():
    """ (private) Genereate the SCIM API access parameters starting from configuration

        Returns:
            access: (dict) access configuration parameters
                    basic auth:
                        'url': url, 
                        'type' : 'basic',
                        'headers': { "Content-Type" : "application/scim+json" }, 
                        'credentials': (touple) from config

                    outh auth:
                        TO BE DEFINED

            None if there are errors
    """

    if 'url' in c.scim_config:
        url = c.scim_config['url']
    else:
        c.logger("No SCIM endpoint URL provided")
        return None

    if 'auth' in c.scim_config and 'type' in c.scim_config['auth'] \
        and c.scim_config['auth']['type'] == 'basic' \
        and 'username' in c.scim_config['auth'] \
        and 'password' in c.scim_config['auth']:

        access = {
            'url': url, 
            'type' : 'basic',
            'headers': { "Content-Type" : "application/scim+json" }, 
            'credentials': (c.scim_config['auth']['username'], c.scim_config['auth']['password'])  # can be credential or token
        }

        return access

    elif 'auth' in c.scim_config and 'type' in c.scim_config['auth'] \
        and c.scim_config['auth']['type'] == 'oauth':

        # TODO: implement oauth method 

        c.logger.error('SCIM outh authentication method not implemented')

        # hyp.:
        # get oauth token and configure headers
        # token  =  oauth_get_token ...
        # access = {
        #     'type' : 'basic',
        #     'headers': { "Content-Type" : "application/scim+jsonn",
        #                  "X-USER-IDENTITY-DOMAIN-NAME" : SCIM_USER,
        #                  "Authorization" : "Bearer "+SCIM_TOKEN
        #      }
        #     'token': token 
        # }
        
        return None

    else:
        c.logger.error('Unmanaged SCIM authentication method or mandatory connection info are omitted')
        return None


def get_scim_users():
    """ Request the SCIM user list stored on the platform

        Returns:
            if resp OK = 20x 
                {'http_status': 20x, 'scim_user_list': {<the list of SCIM users>}} 
                also:
                    updates the common.curr_scim_users dictionary with the response/Resources user list

            if there is an HTTP error resp != 20x
                {'http_status': <HTTP error>, 'scim_user_list': {}}
                also:
                    updates the common.curr_scim_users dictionary = []

            any other errors
                {'http_status': None, 'scim_user_list': {}} 
                also:
                    updates the common.curr_scim_users dictionary = []
        
        Raises:
            all error exceptions 
    """

    c.logger.debug("Invoke SCIM REST API call to get user list")

    access = _get_scim_access_param()
    scim_user_obj = scim.User()
    access['url'] = access['url'] + scim_user_obj.URI 

    c.curr_local_users = [] # reset

    # REST API Calls

    if access['type'] == 'basic':

        try:
            resp = requests.get(access['url'] , 
                                auth=access['credentials'], 
                                headers=access['headers'])
        except requests.exceptions.Timeout:
            # Maybe set up for a retry, or continue in a retry loop
            c.logger.error("Error contacting SCIM service - error: Timeout")
            return {'http_status': None, 'scim_users': {}} 
        except requests.exceptions.TooManyRedirects:
                # Tell the user their URL was bad and try a different one
            c.logger.error("Error contacting SCIM service - error: Too Many Redirects")
            return {'http_status': None, 'scim_users': {}} 
        except requests.exceptions.RequestException as e:
            c.logger.error("Error contacting SCIM service - error: %s", e)
            return {'http_status': None, 'scim_users': {}} 

    else:
        # TODO: implement oauth method 
        c.logger.error('Unmanaged SCIM authentication method')
        return {'http_status': None, 'scim_users': {}} 

    # Manage REST response

    if resp.status_code in [200,201,202]:   # http ok, created, accepted
        curr_scim_user_list = json.loads(resp.text)

        if 'Resources' in curr_scim_user_list:
            c.curr_local_users = curr_scim_user_list['Resources']

        c.logger.debug("HTTP status: %d" % resp.status_code)
        c.logger.debug("Returned SCIM Users count: %d" % len(c.curr_local_users))
        return {'http_status': resp.status_code, 'scim_user_list': curr_scim_user_list}
        
    else:
        c.curr_local_users = [] # reset
        c.logger.error("HTTP error - status: %d" % resp.status_code)
        return {'http_status': resp.status_code, 'scim_user_list': {}}



def exec_scim_user_api_req(user, op='get'):
    """ Calls the get/add/update/delete SCIM APIs for the user

        Args:
            user:   (dict) with the SCIM user attrs. 
                    It will be converted to a SCIM User obj.

            add:    (optional bool) 
                        if 'get' (default) req the fileds of the passed user - id != null
                        if 'add' adds the user - id=null 
                        if 'update' changes fileds of the passed user - id != null
                        if 'delete' deletes the passed user - id != null 
                        Note: current SCIM REST API does not impement DELETE,
                              so DELETE call was replaced by as soft delete with a call: PATCH user(user_id).active=false
                        
        Returns: 
            if op is add, update, delete 
                if resp OK = 20x 
                    {'http_status': 20x, 'scim_user': {<the SIM user dict if retuned>}}

            if op is get
                if resp OK = 20x 
                    {'http_status': 20x, 'scim_user': {<the SIM user dict>}}

            if there is an HTTP error resp != 20x
                {'http_status': <HTTP error>, 'scim_user': {}} 

            any other errors
                {'http_status': None, 'scim_user': {}} 

        Raises:
            all errors exceptions 
    """
    c.logger.debug("Invoke SCIM REST API call to [%s] user: %s" % (op, user))
    
    access = _get_scim_access_param()
    scim_user_obj = scim.User()
    access['url'] = access['url'] + scim_user_obj.URI 

    if access['type'] == 'basic':
        
        # REST API calls
        try:
            if op == 'add':
                user.pop('id', None)
                user_json = json.dumps(user, sort_keys=False)
                scim_user_obj = scim_user_obj.from_json(user_json) # convert
                scim_user_json = scim_user_obj.to_json()
                c.logger.debug("ADD - SCIM User object: %s" % scim_user_json)
                resp = requests.post(access['url'] , 
                                    auth=access['credentials'], 
                                    headers=access['headers'],
                                    data=scim_user_json)
            elif op == 'update':
                id = str(user['id']) 
                user_json = json.dumps(user, sort_keys=False)
                scim_user_obj = scim_user_obj.from_json(user_json) # convert
                scim_user_json = scim_user_obj.to_json()
                c.logger.debug("UPDATE - SCIM User object: %s" % scim_user_json)
                resp = requests.put(access['url'] + '/' + id , 
                                    auth=access['credentials'], 
                                    headers=access['headers'],
                                    data=scim_user_json)
            elif op == 'delete':
                # DELETE of a SCIM user by REST interface is not implemented
                # id = str(user['id']) 
                # c.logger.debug("DELETE - SCIM User id: %s" % id)
                # resp = requests.delete(access['url'] + '/' + id , 
                #                     auth=access['credentials'], 
                #                     headers=access['headers'])

                # soft DELETE with PATCH user(user_id).active = false 
                id = str(user['id']) 
                c.logger.debug("Soft DELETE - PATCH user(user_id).active=false - SCIM User id: %s" % id)

                patch_req = {
                    "schemas": ["urn:ietf:params:scim:api:messages:2.0:PatchOp"],
                    "Operations": [{"op": "replace", "value": {"active": False}}],
                }

                resp = requests.patch(access['url'] + '/' + id , 
                                    auth=access['credentials'], 
                                    headers=access['headers'],
                                    json=patch_req)
            else:
                op='get'
                id = str(user['id']) 
                c.logger.debug("GET - SCIM User id: %s" % id)
                resp = requests.get(access['url'] + '/' + id , 
                                    auth=access['credentials'], 
                                    headers=access['headers'])
    
        except requests.exceptions.Timeout:
            # Maybe set up for a retry, or continue in a retry loop
            c.logger.error("Error contacting SCIM service - error: Timeout")
            return {'http_status': None, 'scim_users': {}} 
        except requests.exceptions.TooManyRedirects:
                # Tell the user their URL was bad and try a different one
            c.logger.error("Error contacting SCIM service - error: Too Many Redirects")
            return {'http_status': None, 'scim_users': {}} 
        except requests.exceptions.RequestException as e:
            c.logger.error("Error contacting SCIM service - error: %s", e)
            return {'http_status': None, 'scim_users': {}} 

    else:
        # TODO: implement oauth method 
        c.logger.error('Unmanaged SCIM authentication method')
        return {'http_status': None, 'scim_user': {}} 
        
    # Manage REST response 

    if op == 'get' and resp.status_code in [200,201,202]:   # http ok, created, accepted
        scim_user = json.loads(resp.text)
        c.logger.debug("HTTP status: %d" % resp.status_code)
        c.logger.debug("Returned SCIM User: %s" % scim_user)
        return {'http_status': resp.status_code, 'scim_user': scim_user} 

    elif op in ['add', 'update', 'delete'] and resp.status_code in [200,201,202]:   # http ok, created, accepted
        scim_user = json.loads(resp.text)
        c.logger.debug("HTTP status: %d" % resp.status_code)
        c.logger.debug("Returned SCIM User: %s" % scim_user)
        return {'http_status': resp.status_code, 'scim_user': scim_user} 

    else:
        c.logger.error("HTTP error - status: %d" % resp.status_code)
        return {'http_status': resp.status_code, 'scim_user': {}} 






