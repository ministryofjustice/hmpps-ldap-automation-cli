from cli import config
from cli.ldap_automation import ldap_connect
from ldap3 import SUBTREE
import click


def test_search():
    ldap_connection = ldap_connect(config.ldap_host, config.ldap_user, config.ldap_password)
    ldap_connection.search(
        "dc=moj,dc=com",
        "(objectClass=*)",
        search_scope=SUBTREE,
        attributes=["*"],
    )
    print(ldap_connection.entries)


@click.command()
def test():
    test_search()
