import click
import cli.ldap.update_user_home_areas

from cli import git

@click.group()
def main_group():
    pass

# Add git test
@click.command()
def git_test():
    git.dl_test()

# Add roles to username
@click.command()
@click.option("--user-ou", help="OU to add users to, defaults to ou=Users", default="ou=Users")
@click.option("--root-dn", help="Root DN to add users to", default="dc=moj,dc=com")
@click.argument("user-role-list", required=True)
def add_roles_to_users(user_ou, root_dn, user_role_list):
    ldap.process_user_roles_list(user_role_list, user_ou, root_dn)

# Update user home area
@click.command()
@click.option("--old-home-area", help="name of old home area")
@click.option("--new-home-area", help="name of new home area")
def update_user_home_areas(old_home_area, new_home_area):
   cli.ldap.update_user_home_areas.update_user_home_areas(old_home_area, new_home_area)

main_group.add_command(git_test)
main_group.add_command(add_roles_to_users)
main_group.add_command(update_user_home_areas)

if __name__ == "__main__":
    main_group()
