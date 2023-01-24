#
# LDAP helper module
#
import codecs
import uuid
import ldap

from libs import common as c

def handle_ldap_entry(entry):
    """ Default LDAP entry handler - logs the user (entry) attributes
        Convert objectGUID, UUID to readable strings.

        Args:
            entry: LDAP user
            
        Returns:
            N/A

        Raises:
            N/A
    """
    
    for k,e in entry.items():
        if k.lower() in ['objectguid', 'uuid']:
            # converts binary guid in a human-readable string
            guid = uuid.UUID(bytes=e[0])
            es = str(guid) 
        else:
            es = codecs.decode(e[0], 'utf-8')

        c.logger.debug("  %-20s %s" % (k, es)) 

def ldap_retrieve_users(ldap_url, 
                        ldap_user, 
                        ldap_password, 
                        user_dn, 
                        user_attr=['cn', 'mail' ,'objectGUID'], 
                        user_filter="", 
                        ldap_tls=False, 
                        handle_entry=handle_ldap_entry):
    """ Get users from an LDAP endpoint
        
        Args:
            ldap_url: URL of the LDAP endpoint (e.g., ldap://hostname...)
            ldap_user: DN of the LDAP user 
            ldap_password: password LDAP user 
            user_dn: users to retrieve DN 
            user_attr: (optional, default: ['cn', 'mail' ,'objectGUID']) list of users' LDAP attributes to retrieve
            user_filter: (optional, default: "") LDAP filter 
            ldap_tls: (optional, default: False) TLS layer active 
            handle_entry: (optional, default: handle_ldap_entry) LDAP entries' processing handler

        Returns:
            True if LDAP retrieval ok
            False if error occurs 

        Raises:
            N/A
    """

    # TODO: activate and test the TLS functionality
    # TODO: export the ldap.SCOPE_SUBTREE as parameter

    try:
        c.logger.debug("Contacting LDAP") 
        l = ldap.initialize(ldap_url)

        l.protocol_version = ldap.VERSION3
        l.simple_bind_s(ldap_user, ldap_password) 

        #this will scope the entire subtree Users
        searchScope = ldap.SCOPE_SUBTREE

        res = l.search_s(user_dn, searchScope, user_filter, user_attr)
    
        for dn, entry in res:
            c.logger.debug('Processing LDAP entry: %s' % dn)
            handle_entry(entry)
        
        l.unbind_s()
        
        return True

    except ldap.INVALID_CREDENTIALS:
        c.logger.error( "Incorrect LDAP credentials" )
        return False

    except ldap.LDAPError as e:
        c.logger.error( e )
        return False
