#
# LDAP plugin common functions
#

import codecs
import uuid

from libs import common as c

def is_ldap_field(value):
    """ Checks if the value is an LDAP field - syntax: ${LDAP_filed_name}

        Args:
            value: LDAP field syntax: ${LDAP_filed_name} string to check
            
        Returns:
            True if LDAP Filed or False otherwise
    """
    return value[0:2] == '${' and value[-1] == '}'

def get_ldap_field(value):
    """ Checks if the value is an LDAP field - syntax: ${LDAP_filed_name}
        and returns the name of the field or the value

        Args:
            value: string to check
            
        Returns:
            LDAP Field name or the value as string in case value in not ${...}
    """
    if is_ldap_field(value):    
        return value[2:-1]
    else:
        return str(value)

def get_config_mapping_value(value, ldap_user):
    """ Interprets values from the mapping configuration ldap_attr_mapping key,
        it returns the yaml value as constant (int/float/str/bool) 
        or the LDAP field content: ${ldap_field} = ldap_user[ldap_field]
        
        All LDAP field contents are converted to UTF-8 string.
        It also convert LDAP field objectGUI and UUID binary content to a human-readable string.
        
        Args:
            value: a yaml const or a ${ldap_field} field name (ldap_user[ldap_field])
            ldap_user: LDAP user containing the ldap_fields

        Returns:
            yaml const (str/int/float/bool) or a ${ldap_field} an ldap_filed.value
            Default: '' if the field does not exist in the ldap_user
    """

    if isinstance(value, (str)):
        if is_ldap_field(value):
            f = get_ldap_field(value)

            # ldap field
            if f in ldap_user:

                if f.lower() in ['objectguid', 'uuid']:
                    # converts binary guid in a human-readable string
                    guid = uuid.UUID(bytes=ldap_user[ f ][0])
                    return str(guid) 
                else:
                    return codecs.decode(ldap_user[ f ][0], 'utf-8').strip()
            else:
                c.logger.error('LDAP field [%s] does not exist in the LDAP User: %s' % (f, ldap_user))
                return ''
        else:
            return str(value).strip()

    elif isinstance(value, (int, float, bool)):
        return value

def scim_common_mapping(k, v, scim_user, ldap_user):
    """ Execute the common mapping for the SCIM keys that are independent on 
        the LDAP vendor

        Args:
            k: SCIM key to map (from config)
            v: const value or LDAP field to map (from config)

            scim_user: the current scim user dict that we are mapping
            ldap_user: the LDAP user to be mapped

        Returns:
            scim_user is the current scim user changed by the function
    """

    if k == 'name.givenName' and is_ldap_field(v):
        # SCIM specifc name field assignment from LDAP (usually) 'givenName' attr.
        # SCIM define name = { givenName: <value>, familyName: <value> }
        if not 'name' in scim_user:
            scim_user['name']={}

        scim_user['name']['givenName'] = get_config_mapping_value(v, ldap_user)

    elif k == 'name.familyName' and is_ldap_field(v):
        # SCIM specifc name field assignment from LDAP (usually) 'sn' attr.
        # SCIM define name = { givenName: <value>, familyName: <value> }
        if not 'name' in scim_user:
            scim_user['name']={}

        scim_user['name']['familyName'] = get_config_mapping_value(v, ldap_user)

    elif k == 'emails.work.value' and is_ldap_field(v):
        # SCIM specifc emails field assignment from LDAP (usually) 'mail' attr.
        # SCIM define emails = [ (value: email addr, type: 'work|home|...', primary: T|F) ]
        email = {
            "value" : get_config_mapping_value(v, ldap_user),
            "type" : "work",
            "primary" : True
        }
        
        scim_user['emails'] = [email]
    
    else:
        # common assignment key, value
        scim_user[k] = get_config_mapping_value(v, ldap_user)
    
    return scim_user