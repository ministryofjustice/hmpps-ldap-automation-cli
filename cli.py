import click


@click.group()
def cli():
    pass


from ldap_automation.add_roles_to_username import add_roles_to_users

cli.add_command(add_roles_to_users)


if __name__ == "__main__":
    cli()
