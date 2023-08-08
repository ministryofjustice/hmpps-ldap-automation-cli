import config
from ldap_automation import ldap_connect
from ldap3 import SUBTREE
import logging

import click


def test():
    ldap_connection = ldap_connect(config.ldap_host, config.ldap_user, config.ldap_password)
    ldap_connection.search(
        "ou=Users,dc=moj,dc=com",
        "(&(cn=*)(objectClass=person))",
        search_scope=SUBTREE,
        attributes=["*"],
    )
    print(ldap_connection.entries)


@click.command()
@click.argument("user-role-list", required=True)
def add_roles_to_users():
    test()
