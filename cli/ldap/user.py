from cli.logging import log
from cli import env

from cli.ldap import ldap_connect
import ldap3
from ldap3 import MODIFY_REPLACE


def change_home_areas(old_home_area, new_home_area, user_ou, root_dn, attribute="userHomeArea", object_class="NDUser"):
    log.info(f"Updating user home areas from {old_home_area} to {new_home_area}")
    ldap_connection = ldap_connect(
        env.vars.get("LDAP_HOST"), env.vars.get("LDAP_USER"), env.secrets.get("LDAP_BIND_PASSWORD")
    )

    search_filter = (
        f"(&(objectclass={object_class})(userHomeArea={old_home_area})(!(cn={old_home_area}))(!(endDate=*)))"
    )
    ldap_connection.search(",".join([user_ou, root_dn]), search_filter, attributes=[attribute])

    # Iterate through the search results and update the attribute
    for entry in ldap_connection.entries:
        dn = entry.entry_dn
        changes = {attribute: [(MODIFY_REPLACE, [new_home_area])]}
        ldap_connection.modify(dn, changes)

        # Check if the modification was successful
        if ldap_connection.result["result"] == 0:
            log.info(f"Successfully updated {attribute} for {dn}")
        else:
            log.error(f"Failed to update {attribute} for {dn}: {ldap_connection.result}")


def update_roles(old_role, new_role, user_ou, root_dn, user_filter="(objectclass=*)", role_filter="(objectclass=*)"):
    log.info(f"Updating user roles from {old_role} to {new_role}")
    ldap_connection = ldap_connect(
        env.vars.get("LDAP_HOST"), env.vars.get("LDAP_USER"), env.secrets.get("LDAP_BIND_PASSWORD")
    )

    # Search for users with the old role
