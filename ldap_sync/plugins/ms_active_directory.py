#
# Microsoft Active Directory LDAP plugin
# This plugin manages the MLDE mapping and MS A/D specificities 
#
# ref :https://learn.microsoft.com/en-us/troubleshoot/windows-server/identity/useraccountcontrol-manipulate-account-properties

import sys
import codecs

from libs import ldap_helper as lh
from libs import common as c
from libs import ldap_plugin_common as lpc

def init(*args, **kwargs):
    """ Module init not implemented
    """
    c.logger.debug("%s %s" % (args, kwargs))

def main(*args, **kwargs):
    """ Module main not implemented
    """
    c.logger.debug("%s %s" % (args, kwargs))

def ldap_get_users():
    """ Wrapper of the LDAP retrieve call
        To be used in case the standard parameters or the access method does not fit the need.
    """

    # get LDAP users

    c.ldap_users = [] # reset

    resp_ok = lh.ldap_retrieve_users(   c.ldap_config_auth['url'],
                                        c.ldap_config_auth['user'],
                                        c.ldap_config_auth['password'],
                                        c.ldap_config_users['dn'],
                                        c.ldap_config_users['attr'],
                                        c.ldap_config_users['filter'],
                                        c.ldap_config_auth['tls'], 
                                        handle_entry = c.ldap_plugin.ldap_user_handler
                                        )
    
    return resp_ok

def ldap_user_handler(entry):
    """ Process each LDAP entry creating an ldap_users[] item

        Args:
            entry: LDAP user entry
    """
    ldap_user = {} 
    for k, e in entry.items():
        ldap_user[k] = e    # raw

    c.ldap_users.append(ldap_user)
    c.logger.debug("Retrieved LDAP User info: %s" % ldap_user)     
 
def ldap_to_scim_mapping():
    """ MS A/D LDAP to SCIM mapping function.
        Create the SCIM users list mapping the existing LDAP users

        MS A/D Specific LDAP fields management:
            - MS A/D LDAP: userAccount control -> SCIM: active
            - MS A/D LDAP: memberOf -> SCIM memberOf

        Common SCIM LDAP fields management:
            - MS A/D LDAP: objectGUID, UUID -> SCIM: externalId (readable str conversion)
            - MS A/D LDAP: mail -> SCIM: emails = [{value: <email addr>, type: 'work', primary: True}] = emails.work.value
            - MS A/D LDAP: first/last name (givenName/sn) -> SCIM: name: name = { givenName: <value>, familyName: <value> }
    """
    c.logger.debug("Mapping - LDAP Users count: %d" % len(c.ldap_users))
    
    c.local_users = [] # reset

    for ldap_user in c.ldap_users:
        c.logger.debug("Mapping - LDAP User info: %s" % ldap_user)

        scim_user = {}
        
        for k,v in c.scim_config['attr_mapping'].items():
            # k = SCIM side, v = LDAP field or const

            if k == 'active' and v.lower() == '${useraccountcontrol}':
                # MS A/D specific userAccountControl binary flag (0x0002) => ACCOUNT DISABLE
                # conversion to the SCIM 'active' filed spec (bool)
                account_disable =  bool( int(lpc.get_config_mapping_value(v, ldap_user)) & 0x0002 )      # bit 2 ACCOUNTDISABLE
                if account_disable:
                    scim_user[k] = False
                else:
                    scim_user[k] = True

            elif k == 'memberOf' and  lpc.is_ldap_field(v):
                # MS A/D specific membersOf field (probably not the only in MS A/D) 
                # memebersOf of is a list of groups DN
                scim_user[k] = list(map(lambda x: codecs.decode(x, 'utf-8'), ldap_user[lpc.get_ldap_field(v)]))  # list of groups

            else:
                # SCIM common 
                scim_user = lpc.scim_common_mapping(k, v, scim_user, ldap_user)

        c.logger.debug("Mapping - SCIM User info: %s" % scim_user)
        c.local_users.append(scim_user)
    
    c.logger.debug("Mapping - SCIM Users count: %d" % len(c.local_users))


def ldap_to_det_mapping():
    """ MS A/D LDAP to Determined APIs mapping function.
        Create the Determined APIs users list mapping the existing LDAP users

        VERIFY THESE BELOW !!!! 
                    MS A/D Specific LDAP fields management:
                        - MS A/D LDAP: userAccount control -> SCIM: active
                        - MS A/D LDAP: memberOf -> SCIM memberOf

                    Common SCIM LDAP fields management:
                        - MS A/D LDAP: objectGUID, UUID -> SCIM: externalId (readable str conversion)
                        - MS A/D LDAP: mail -> SCIM: emails = [{value: <email addr>, type: 'work', primary: True}] = emails.work.value
                        - MS A/D LDAP: first/last name (givenName/sn) -> SCIM: name: name = { givenName: <value>, familyName: <value> }
    """
    ...