from cli.logging import log
from cli import env
from cli.ldap import ldap_connect


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
