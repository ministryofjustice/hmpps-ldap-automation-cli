import logging

from cli import config
from cli.ldap import ldap_connect
import ldap3
from ldap3 import MODIFY_REPLACE


def update_user_home_areas(old_home_area, new_home_area, attribute="userHomeArea"):
        logging.info(f"Updating user home areas from {old_home_area} to {new_home_area}")
        conn = ldap_connect(config.ldap_host, config.ldap_user, config.ldap_password)

        base_dn = "ou=Users,dc=moj,dc=com" # change this
        search_filter = f"'(&(objectclass=NDUser)(userHomeArea={old_home_area})(!(cn={old_home_area}))(!(endDate=*)))'" # and this
        conn.search(base_dn, search_filter, attributes=[attribute])

        # Iterate through the search results and update the attribute
        for entry in conn.entries:
            dn = entry.entry_dn
            changes = {attribute: [(MODIFY_REPLACE, [new_home_area])]}
            conn.modify(dn, changes)

            # Check if the modification was successful
            if conn.result['result'] == 0:
                print(f'Successfully updated {attribute} for {dn}')
            else:
                print(f'Failed to update {attribute} for {dn}: {conn.result}')