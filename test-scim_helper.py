#
# SCIM helper testing
#
import json

from libs import common as c
from libs import scim 
from libs import scim_helper as sh


def main_test():
    c.init()
 
    ###########################################
    # Test SCIM helper

    c.logger.info(80*"=")
    c.logger.info("SCIM helper unit test - start")
    

    # get users
    c.logger.info(80*"-")
    c.logger.info("Get SCIM User list")
    
    _st = c.start_time()

    res = sh.get_scim_users()
    
    c.logger.info("Execution: " + c.stop_time(_st, to_str=True))

    c.logger.info("Get SCIM User list response: %s" % res)
    c.logger.info("### Correct output: {'http_status': 20x, 'scim_user_list': {<the list of SCIM users>}}")

    # add users
    c.logger.info(80*"-")
    c.logger.info("Add SCIM User")

    user = {
            "userName": "user1@domain.intenal",
            "displayName": "user one",
            "name": {
                "givenName"  : "User-First-Name",
                "familyName" : "User-Last-Name",
            },
            "externalId" : "F9168C5E-CEB2-4faa-B6BF-329BF39FA1E4",
            "emails": [{
                "value" : "user-1@domain.intenal",
                "type" : "work",
                "primary" : True
            }],
            "active": True
    }
   
    c.logger.info("User object: %s" % user)
  
    _st = c.start_time()

    res = sh.exec_scim_user_api_req(user, op='add')

    c.logger.info("Execution: " + c.stop_time(_st, to_str=True))
    c.logger.info("SCIM API req. response: %s" % res)
    
    if res['http_status'] == 201: # created
        id = res['scim_user']['id']
    
        c.logger.info("User ID for the next steps: %s" % id)
    
    c.logger.info("### Correct output: {'http_status': 20x, 'scim_user': {<the SCIM user>}} --- if the user exists already http_status = 409")
    
    # update user
    c.logger.info(80*"-")
    c.logger.info("UPDATE SCIM User")

    user = {
            'id': '715509db-132c-4889-b733-bdb6714c69b5',
            "userName": "user1@domain.intenal",
            "displayName": "user two",
            "name": {
                "givenName"  : "User-First-Name",
                "familyName" : "User-Last-Name",
            },
            "externalId" : "222168C5E-CEB2-4faa-B6BF-329BF39FA1E4",
            "emails": [{
                "value" : "user1@domain.intenal",
                "type" : "work",
                "primary" : True
            }],
            "active": True
    }
   
    c.logger.info("User object: %s" % user)
  
    _st = c.start_time()

    res = sh.exec_scim_user_api_req(user, op='update')

    c.logger.info("Execution: " + c.stop_time(_st, to_str=True))
    c.logger.info("SCIM API req. response: %s" % res)
    
      
    # delete user

    user = {
            'id': '715509db-132c-4889-b733-bdb6714c69b5',
    }
   
    c.logger.info("User object: %s" % user)
  
    _st = c.start_time()

    res = sh.exec_scim_user_api_req(user, op='delete')

    c.logger.info("Execution: " + c.stop_time(_st, to_str=True))
    c.logger.info("SCIM API req. response: %s" % res)
    
    c.logger.info("SCIM helper unit test - end")


   
    

if __name__ == "__main__":
    main_test()