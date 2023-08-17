import re

import ldap3.utils.hashed
from cli.ldap import ldap_connect
from cli import env
import cli.git as git
import glob
from cli.logging import log
from pathlib import Path
import cli.template
from ldif import LDIFParser


def get_repo():
    app_id = env.vars.get("GH_APP_ID")
    private_key = env.vars.get("GH_PRIVATE_KEY")
    installation_id = env.vars.get("GH_INSTALLATION_ID")
    # url = 'https://github.com/ministryofjustice/hmpps-delius-pipelines.git'
    url = "https://github.com/ministryofjustice/hmpps-ndelius-rbac.git"
    token = git.get_access_token(app_id, private_key, installation_id)
    try:
        repo = git.get_repo(url, token=token, dest_name="rbac")
        return repo
    except Exception as e:
        log.exception(e)
        return None


def prep_for_templating(files, strings=None):
    if strings is None:
        strings = env.vars.get("RBAC_SUBSTITUTIONS")
    # get a list of files
    # print(strings)
    # print(type(strings))
    for file_path in files:
        file = Path(file_path)
        for k, v in strings.items():
            print("replacing", k, "with", v, "in", file_path)
            # print(
            #     file.read_text().replace(k, v),
            # )
            file.write_text(
                file.read_text().replace(k, v),
            )


def template_rbac(files):
    hashed_pwd_admin_user = ldap3.utils.hashed.hashed(ldap3.HASHED_SALTED_SHA, env.secrets.get("LDAP_ADMIN_PASSWORD"))
    rendered_files = []
    for file in files:
        rendered_text = cli.template.render(
            file,
            ldap_config=env.vars.get("LDAP_CONFIG"),
            bind_password_hash=hashed_pwd_admin_user,
            secrets=env.secrets,
            ssm_prefix=env.vars.get("SSM_PREFIX"),
            oasys_password=env.secrets.get("OASYS_PASSWORD"),
            environment_name=env.vars.get("ENVIRONMENT_NAME"),
            project_name=env.vars.get("PROJECT_NAME"),
        )
        rendered_file = cli.template.save(rendered_text, file)
        rendered_files.append(rendered_file)
    return rendered_files


def context_ldif(rendered_files):
    context_file = [file for file in rendered_files if "context" in file][0]
    parser = LDIFParser(open(context_file, "rb"), strict=False)
    for dn, record in parser.parse():
        print("got entry record: %s" % dn)
        print(record)
        ldap_connection = ldap_connect(
            env.vars.get("LDAP_HOST"), env.vars.get("LDAP_USER"), env.secrets.get("LDAP_PASSWORD")
        )
        ldap_connection.add(dn, attributes=record)


def group_ldifs(rendered_files):
    # connect to ldap
    ldap_connection = ldap_connect(
        env.vars.get("LDAP_HOST"), env.vars.get("LDAP_USER"), env.secrets.get("LDAP_PASSWORD")
    )
    group_files = [file for file in rendered_files if "groups" in file]
    # loop through the group files
    for file in group_files:
        # parse the ldif into dn and record
        parser = LDIFParser(open(file, "rb"), strict=False)
        # loop through the records
        for dn, record in parser.parse():
            print("got entry record: %s" % dn)
            # print(record)
            # add the record to ldap
            ldap_connection.add(dn, attributes=record)
            ldap_connection.modify(dn, {"description": [(ldap3.MODIFY_REPLACE, record["description"])]})


def policy_ldifs(rendered_files):
    # connect to ldap
    ldap_connection = ldap_connect(
        env.vars.get("LDAP_HOST"), env.vars.get("LDAP_USER"), env.secrets.get("LDAP_PASSWORD")
    )
    policy_files = [file for file in rendered_files if "policy" in file]

    # first, delete the policies
    ldap_connection.delete("ou=Policies," + env.vars.get("LDAP_CONFIG").get("base_root"))

    # loop through the policy files
    for file in policy_files:
        # parse the ldif into dn and record
        parser = LDIFParser(open(file, "rb"), strict=False)
        # loop through the records
        for dn, record in parser.parse():
            print("got entry record: %s" % dn)
            # print(record)
            # add the record to ldap
            ldap_connection.add(dn, attributes=record)


def role_ldifs(rendered_files):
    # connect to ldap
    ldap_connection = ldap_connect(
        env.vars.get("LDAP_HOST"), env.vars.get("LDAP_USER"), env.secrets.get("LDAP_PASSWORD")
    )
    role_files = [file for file in rendered_files if "nd_role" in file]

    # first, delete the roles
    ldap_connection.delete("cn=ndRoleCatalogue," + env.vars.get("LDAP_CONFIG").get("base_users"))
    ldap_connection.delete("cn=ndRoleGroups," + env.vars.get("LDAP_CONFIG").get("base_users"))

    # ensure boolean values are Uppercase..
    # (not yet implemented, probably not needed)

    # loop through the role files
    for file in role_files:
        # parse the ldif into dn and record
        parser = LDIFParser(open(file, "rb"), strict=False)
        # loop through the records
        for dn, record in parser.parse():
            print("got entry record: %s" % dn)
            # print(record)
            # add the record to ldap
            ldap_connection.add(dn, attributes=record)


# not complete!!
# see https://github.com/ministryofjustice/hmpps-delius-pipelines/blob/master/components/delius-core/playbooks/rbac/import_schemas.yml
def schema_ldifs(rendered_files):
    # connect to ldap
    ldap_connection = ldap_connect(
        env.vars.get("LDAP_HOST"), env.vars.get("LDAP_USER"), env.secrets.get("LDAP_PASSWORD")
    )

    schema_files = [file for file in rendered_files if "delius.ldif" or "pwm.ldif" in file]

    # loop through the schema files
    for file in schema_files:
        # parse the ldif into dn and record
        parser = LDIFParser(open(file, "rb"), strict=False)
        # loop through the records
        for dn, record in parser.parse():
            print("got entry record: %s" % dn)
            # print(record)
            # add the record to ldap
            ldap_connection.add(dn, attributes=record)


def user_ldifs(rendered_files):
    # connect to ldap
    ldap_connection = ldap_connect(
        env.vars.get("LDAP_HOST"), env.vars.get("LDAP_USER"), env.secrets.get("LDAP_PASSWORD")
    )
    user_files = [file for file in rendered_files if "-users" in file]

    # first, delete the users
    for file in user_files:
        # parse the ldif into dn and record
        parser = LDIFParser(open(file, "rb"), strict=False)
        # loop through the records
        for dn, record in parser.parse():
            print("got entry record: %s" % dn)
            # print(record)
            # add the record to ldap
            ldap_connection.delete(dn)

    # loop through the user files
    for file in user_files:
        # parse the ldif into dn and record
        parser = LDIFParser(open(file, "rb"), strict=False)
        # loop through the records
        for dn, record in parser.parse():
            print("got entry record: %s" % dn)
            # print(record)
            # add the record to ldap
            ldap_connection.add(dn, attributes=record)


def test():
    repo = get_repo()
    print(env.vars.get("RBAC_SUBSTITUTIONS"))
    dir = "./rbac"

    files = [
        file
        for file in glob.glob(f"{dir}/**/*", recursive=True)
        if Path(file).is_file() and Path(file).name.endswith(".ldif") or Path(file).name.endswith(".j2")
    ]

    prep_for_templating(files)

    ldap_adds = ["context.ldif"]
    ldap_modifies = []

    rendered_files = template_rbac(files)
    parser = LDIFParser(open("./rendered/rbac/context.ldif", "rb"), strict=False)
    for dn, record in parser.parse():
        print("got entry record: %s" % dn)
        print(record)
        ldap_connection = ldap_connect(
            env.vars.get("LDAP_HOST"), env.vars.get("LDAP_USER"), env.secrets.get("LDAP_PASSWORD")
        )
        ldap_connection.add(dn, attributes=record)
