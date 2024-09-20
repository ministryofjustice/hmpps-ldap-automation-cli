import click
import cli.ldap_cmds.rbac
import cli.ldap_cmds.user

from cli import (
    logger,
)


@click.group()
def main_group():
    pass


@click.command()
@click.option(
    "-u",
    "--user-ou",
    help="OU to add users to, defaults to ou=Users",
    default="ou=Users",
)
@click.option(
    "-r",
    "--root-dn",
    help="Root DN to add users to",
    default="dc=moj,dc=com",
)
@click.argument(
    "user-role-list",
    required=True,
)
def add_roles_to_users(
    user_ou,
    root_dn,
    user_role_list,
):
    cli.ldap_cmds.user.process_user_roles_list(
        user_role_list,
        user_ou,
        root_dn,
    )


# Update user home area
@click.command()
@click.option(
    "-o",
    "--old-home-area",
    help="name of old home area",
    required=True,
)
@click.option(
    "-n",
    "--new-home-area",
    help="name of new home area",
    required=True,
)
@click.option(
    "-u",
    "--user-ou",
    help="OU to add users to, defaults to ou=Users",
    default="ou=Users",
)
@click.option(
    "-r",
    "--root-dn",
    help="Root DN to add users to, defaults to dc=moj,dc=com",
    default="dc=moj,dc=com",
)
def update_user_home_areas(
    old_home_area,
    new_home_area,
    user_ou,
    root_dn,
):
    cli.ldap_cmds.user.change_home_areas(
        old_home_area,
        new_home_area,
        user_ou,
        root_dn,
    )


# Update user roles
@click.command()
@click.argument(
    "roles",
    required=True,
)
@click.argument(
    "user-note",
    required=False,
)
@click.option(
    "-u",
    "--user-ou",
    help="OU to add users to, defaults to ou=Users",
    default="ou=Users",
)
@click.option(
    "-r",
    "--root-dn",
    help="Root DN to add users to, defaults to dc=moj,dc=com",
    default="dc=moj,dc=com",
)
@click.option(
    "--add",
    help="Add role to users",
    is_flag=True,
)
@click.option(
    "--remove",
    help="Remove role from users",
    is_flag=True,
)
@click.option(
    "--update-notes",
    help="Remove role from users",
    is_flag=True,
)

@click.option(
    "-uf",
    "--user-filter",
    help="Filter to find users",
    required=False,
    default="(objectclass=*)",
)
@click.option("--roles-to-filter", help="Roles to filter", required=False, default="*")
def update_user_roles(
    roles,
    user_ou,
    root_dn,
    add,
    remove,
    update_notes,
    user_note,
    user_filter,
    roles_to_filter,
):


@click.command()
@click.option(
    "-t",
    "--rbac-repo-tag",
    help="RBAC repo tag to use",
    default="master",
)
def rbac_uplift(
    rbac_repo_tag,
):
    cli.ldap_cmds.rbac.main(rbac_repo_tag)


@click.command()
@click.option(
    "-u",
    "--user-ou",
    help="OU to add users to, defaults to ou=Users",
    default="ou=Users",
)
@click.option(
    "-r",
    "--root-dn",
    help="Root DN to add users to, defaults to dc=moj,dc=com",
    default="dc=moj,dc=com",
)
def deactivate_crc_users(
    user_ou,
    root_dn,
):
    cli.ldap_cmds.user.deactivate_crc_users(
        user_ou,
        root_dn,
    )


@click.command()
@click.option(
    "-u",
    "--user-ou",
    help="OU to add users to, defaults to ou=Users",
    default="ou=Users",
)
@click.option(
    "-r",
    "--root-dn",
    help="Root DN to add users to, defaults to dc=moj,dc=com",
    default="dc=moj,dc=com",
)
def user_expiry(user_ou, root_dn):
    cli.ldap_cmds.user.user_expiry(user_ou=user_ou, root_dn=root_dn)


@click.command()
@click.option(
    "-u",
    "--user-ou",
    help="OU to add users to, defaults to ou=Users",
    default="ou=Users",
)
@click.option(
    "-r",
    "--root-dn",
    help="Root DN to add users to, defaults to dc=moj,dc=com",
    default="dc=moj,dc=com",
)
def remove_all_user_passwords(user_ou, root_dn):
    cli.ldap_cmds.user.remove_all_user_passwords(user_ou=user_ou, root_dn=root_dn)


# from cli.ldap import test

main_group.add_command(add_roles_to_users)
main_group.add_command(rbac_uplift)
main_group.add_command(update_user_home_areas)
main_group.add_command(update_user_roles)
main_group.add_command(deactivate_crc_users)
main_group.add_command(user_expiry)
main_group.add_command(remove_all_user_passwords)

logger.configure_logging()

if __name__ == "__main__":
    main_group()
