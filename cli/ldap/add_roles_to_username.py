import logging

from cli import config
from cli.ldap import ldap_connect


def parse_user_role_list(user_role_list):
    return {user.split(",")[0]: user.split(",")[1].split(";") for user in user_role_list.split("|")}


def add_roles_to_user(username, roles, user_ou="ou=Users", root_dn="dc=moj,dc=com"):
    logging.info(f"Adding roles {roles} to user {username}")
    ldap_connection = ldap_connect(config.ldap_host, config.ldap_user, config.ldap_password)
    for role in roles:
        ldap_connection.add(
            f"cn={role},cn={username},{user_ou},{root_dn}",
            attributes={
                "objectClass": ["NDRoleAssociation", "alias"],
                "aliasedObjectName": f"cn={role},cn={username},cn=ndRoleCatalogue,{root_dn}",
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
    user_roles = parse_user_role_list(user_role_list)
    for user, roles in user_roles.items():
        add_roles_to_user(user, roles, user_ou, root_dn)
