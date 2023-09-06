import click
import cli.ldap.rbac, cli.ldap.user

from cli import git, logger


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
@click.argument("user-note", required=False)
@click.option("-u", "--user-ou", help="OU to add users to, defaults to ou=Users", default="ou=Users")
@click.option("-r", "--root-dn", help="Root DN to add users to, defaults to dc=moj,dc=com", default="dc=moj,dc=com")
@click.option("--add", help="Add role to users", is_flag=True)
@click.option("--remove", help="Remove role from users", is_flag=True)
@click.option("--update-notes", help="Remove role from users", is_flag=True)
@click.option(
    "-rf",
    "--role-filter",
    help='Comma seperated string to generate roles filter from eg "role1,role2,role3"',
    required=False,
    default="*",
)
@click.option("-uf", "--user-filter", help="Filter to find users", required=False, default="(userSector=*)")
def update_user_roles(roles, user_ou, root_dn, add, remove, update_notes, user_note, user_filter, role_filter):
    cli.ldap.user.update_roles(
        roles,
        user_ou,
        root_dn,
        add,
        remove,
        update_notes,
        user_note=user_note,
        user_filter=user_filter,
        role_filter=role_filter,
    )


@click.command()
@click.option("-t", "--rbac-repo-tag", help="RBAC repo tag to use", default="master")
def rbac_uplift(rbac_repo_tag):
    cli.ldap.rbac.main(rbac_repo_tag)


@click.command()
@click.option("-u", "--user-ou", help="OU to add users to, defaults to ou=Users", default="ou=Users")
@click.option("-r", "--root-dn", help="Root DN to add users to, defaults to dc=moj,dc=com", default="dc=moj,dc=com")
def deactivate_crc_users(user_ou, root_dn):
    cli.ldap.user.deactivate_crc_users(user_ou, root_dn)


# from cli.ldap import test

main_group.add_command(add_roles_to_users)
main_group.add_command(rbac_uplift)
main_group.add_command(update_user_home_areas)
main_group.add_command(update_user_roles)

logger.configure_logging()

if __name__ == "__main__":
    main_group()
