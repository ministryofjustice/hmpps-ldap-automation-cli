import cli.ldap

from cli.logger import log
from cli import env

from cli.ldap import ldap_connect
from ldap3 import MODIFY_REPLACE, DEREF_NEVER

import cli.database
from itertools import product


#########################################
# Change a users home area
#########################################
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


#########################################
#  Add roles to a user
#########################################


def parse_user_role_list(user_role_list):
    # The format of the list should be a pipe separated list of username and role lists,
    # where the username and role list is separated by a comma character,
    # and the roles are separated by a semi-colon:
    # username1,role1;role2;role3|username2,role1;role2

    return {user.split(",")[0]: user.split(",")[1].split(";") for user in user_role_list.split("|")}


def add_roles_to_user(username, roles, user_ou="ou=Users", root_dn="dc=moj,dc=com"):
    log.info(f"Adding roles {roles} to user {username}")
    ldap_connection = ldap_connect(
        env.vars.get("LDAP_HOST"), env.vars.get("LDAP_USER"), env.secrets.get("LDAP_BIND_PASSWORD")
    )
    for role in roles:
        ldap_connection.add(
            f"cn={role},cn={username},{user_ou},{root_dn}",
            attributes={
                "objectClass": ["NDRoleAssociation", "alias"],
                "aliasedObjectName": f"cn={role},cn={username},cn=ndRoleCatalogue,{user_ou},{root_dn}",
            },
        )
        if ldap_connection.result["result"] == 0:
            print(f"Successfully added role {role} to user {username}")
        elif ldap_connection.result["result"] == 68:
            print(f"Role {role} already exists for user {username}")
        else:
            print(ldap_connection.result)
            print(ldap_connection.response)
            raise Exception(f"Failed to add role {role} to user {username}")


def process_user_roles_list(user_role_list, user_ou="ou=Users", root_dn="dc=moj,dc=com"):
    log.info(f"secrets: {env.secrets}")
    user_roles = parse_user_role_list(user_role_list)
    for user, roles in user_roles.items():
        add_roles_to_user(user, roles, user_ou, root_dn)


#########################################
#  Update user roles
#########################################


def update_roles(
    roles,
    user_ou,
    root_dn,
    add,
    remove,
    update_notes,
    user_notes="User roles updated by Delius Script",
    user_filter="(userSector=*)",
    role_filter="*",
):
    ldap_connection_user_filter = ldap_connect(
        env.vars.get("LDAP_HOST"), env.vars.get("LDAP_USER"), env.secrets.get("LDAP_BIND_PASSWORD")
    )

    # # Search for users matching the user_filter
    ldap_connection_user_filter.search(",".join([user_ou, root_dn]), user_filter, attributes=["cn"])
    users_found = sorted([entry.cn.value for entry in ldap_connection_user_filter.entries if entry.cn.value])
    log.debug("users found from user filter")
    log.debug(users_found)
    ldap_connection_user_filter.unbind()

    roles_filter_list = role_filter.split(",")
    roles = roles.split(",")

    # create role filter
    if len(roles_filter_list) > 0:
        full_role_filter = (
            f"(&(objectclass=NDRoleAssociation)(|{''.join(['(cn=' + role + ')' for role in roles_filter_list])}))"
        )
    else:
        full_role_filter = "(&(objectclass=NDRoleAssociation)(cn=*))"

    # Search for roles matching the role_filter
    ldap_connection_role_filter = ldap_connect(
        env.vars.get("LDAP_HOST"), env.vars.get("LDAP_USER"), env.secrets.get("LDAP_BIND_PASSWORD")
    )

    ldap_connection_role_filter.search(
        ",".join([user_ou, root_dn]),
        full_role_filter,
        attributes=["cn"],
        dereference_aliases=DEREF_NEVER,
    )
    roles_found = sorted(
        list(set([entry.entry_dn.split(",")[1].split("=")[1] for entry in ldap_connection_role_filter.entries]))
    )
    log.debug("users found from roles filter: ")
    log.debug(roles_found)

    ldap_connection_role_filter.unbind()

    # generate a list of matches in roles and users
    matched_users = set(users_found) & set(roles_found)
    log.debug("matched users: ")
    log.debug(matched_users)

    # cartesian_product = [(user, role) for user in matched_users for role in roles]

    cartesian_product = list(product(matched_users, roles))
    log.debug("cartesian product: ")
    log.debug(cartesian_product)

    ldap_connection_action = ldap_connect(
        env.vars.get("LDAP_HOST"), env.vars.get("LDAP_USER"), env.secrets.get("LDAP_BIND_PASSWORD")
    )

    for item in cartesian_product:
        if add:
            ldap_connection_action.add(
                f"cn={item[1]},cn={item[0]},{user_ou},{root_dn}",
                attributes={
                    "cn": item[1],
                    "aliasedObjectName": f"cn={item[1]},cn=ndRoleCatalogue,{user_ou},{root_dn}",
                    "objectClass": ["NDRoleAssociation", "alias", "top"],
                },
            )
            if ldap_connection_action.result["result"] == 0:
                log.info(f"Successfully added role '{item[1]}' to user '{item[0]}'")
            elif ldap_connection_action.result["result"] == 68:
                log.info(f"Role '{item[1]}' already present for user '{item[0]}'")
            else:
                log.error(f"Failed to add role '{item[1]}' to user '{item[0]}'")
                log.debug(ldap_connection_action.result)
        elif remove:
            ldap_connection_action.delete(f"cn={item[1]},cn={item[0]},{user_ou},{root_dn}")
            if ldap_connection_action.result["result"] == 0:
                log.info(f"Successfully removed role '{item[1]}' from user '{item[0]}'")
            elif ldap_connection_action.result["result"] == 32:
                log.info(f"Role '{item[1]}' already absent for user '{item[0]}'")
            else:
                log.error(f"Failed to remove role '{item[1]}' from user '{item[0]}'")
                log.debug(ldap_connection_action.result)
        else:
            log.error("No action specified")

    if update_notes:
        connection = cli.database.connection()
        cursor = connection.cursor()
        log.debug("Created database cursor successfully")
        for user in matched_users:
            try:
                update_sql = f"UPDATE USER_ SET LAST_UPDATED_DATETIME=CURRENT_DATE, LAST_UPDATED_USER_ID=4 WHERE UPPER(DISTINGUISHED_NAME)=UPPER(:1)"
                insert_sql = f"INSERT INTO USER_NOTE (USER_NOTE_ID, USER_ID, LAST_UPDATED_USER_ID, LAST_UPDATED_DATETIME, NOTES) SELECT user_note_id_seq.nextval, (select USER_ID from USER_ WHERE UPPER(DISTINGUISHED_NAME)=UPPER(:1)), 4, sysdate, :2, FROM dual;"
                cursor.execute(update_sql, (user,))
                cursor.execute(insert_sql, (user, user_notes))
                log.info(f"Updated notes for user {user}")
            except:
                log.exception(f"Failed to update notes for user {user}")
        connection.commit()
        log.info("Committed changes to database successfully")
        connection.close()
