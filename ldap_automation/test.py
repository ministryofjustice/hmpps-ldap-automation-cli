import config
from ldap_automation import ldap_connect
import logging

import click


def test():
    ldap_connection = ldap_connect(config.ldap_host, config.ldap_user, config.ldap_password)
    logging.


@click.command()
@click.argument("user-role-list", required=True)
def add_roles_to_users():
    test()
