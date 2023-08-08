import click


@click.group()
def main_group():
    pass


from cli.ldap_automation.add_roles_to_username import add_roles_to_users
from cli.ldap_automation.test import test

main_group.add_command(add_roles_to_users)
main_group.add_command(test)

if __name__ == "__main__":
    main_group()
