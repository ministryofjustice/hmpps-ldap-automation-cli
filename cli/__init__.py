import click
import cli.ldap.add_roles_to_username, cli.ldap.rbac, cli.ldap.user

from cli import git
import cli.env


@click.group()
def main_group():
    pass


@click.command()
@click.option("-u", "--user-ou", help="OU to add users to, defaults to ou=Users", default="ou=Users")
@click.option("-r", "--root-dn", help="Root DN to add users to", default="dc=moj,dc=com")
@click.argument("user-role-list", required=True)
def add_roles_to_users(user_ou, root_dn, user_role_list):
    cli.ldap.user.process_user_roles_list(user_role_list, user_ou, root_dn)


# Update user home area
@click.command()
@click.option("-o", "--old-home-area", help="name of old home area", required=True)
@click.option("-n", "--new-home-area", help="name of new home area", required=True)
@click.option("-u", "--user-ou", help="OU to add users to, defaults to ou=Users", default="ou=Users")
@click.option("-r", "--root-dn", help="Root DN to add users to, defaults to dc=moj,dc=com", default="dc=moj,dc=com")
def update_user_home_areas(old_home_area, new_home_area, user_ou, root_dn):
    cli.ldap.user.change_home_areas(old_home_area, new_home_area, user_ou, root_dn)


# Update user roles
@click.command()
@click.argument("roles", required=True)
@click.argument("user-notes", required=False)
@click.option("-u", "--user-ou", help="OU to add users to, defaults to ou=Users", default="ou=Users")
@click.option("-r", "--root-dn", help="Root DN to add users to, defaults to dc=moj,dc=com", default="dc=moj,dc=com")
@click.option("--add", help="Add role to users", is_flag=True)
@click.option("--remove", help="Remove role from users", is_flag=True)
@click.option("--update-notes", help="Remove role from users", is_flag=True)
def update_user_roles(roles, user_ou, root_dn, add, remove, update_notes, user_notes):
    cli.ldap.user.update_roles(roles, user_ou, root_dn, add, remove, update_notes, user_notes=user_notes)


@click.command()
@click.option("-t", "--rbac-repo-tag", help="RBAC repo tag to use", default="master")
def rbac_uplift(rbac_repo_tag):
    cli.ldap.rbac.main(rbac_repo_tag)


# from cli.ldap import test

main_group.add_command(add_roles_to_users)
main_group.add_command(rbac_uplift)
main_group.add_command(update_user_home_areas)
main_group.add_command(update_user_roles)

if __name__ == "__main__":
    main_group()
