import click
import cli.ldap.add_roles_to_username

from cli import git


@click.group()
def main_group():
    pass


@click.command()
@click.option("--user-ou", help="OU to add users to, defaults to ou=Users", default="ou=Users")
@click.option("--root-dn", help="Root DN to add users to", default="dc=moj,dc=com")
@click.argument("user-role-list", required=True)
def add_roles_to_users(user_ou, root_dn, user_role_list):
    cli.ldap.add_roles_to_username.process_user_roles_list(user_role_list, user_ou, root_dn)


@click.command()
def git_test():
    git.dl_test()


# from cli.ldap import test

main_group.add_command(add_roles_to_users)
main_group.add_command(git_test)

if __name__ == "__main__":
    main_group()
