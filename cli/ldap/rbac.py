import ldap3.utils.hashed
from cli.ldap import (
    ldap_connect,
)
from cli import (
    env,
)
import cli.git as git
import glob
from cli.logger import (
    log,
)
from pathlib import (
    Path,
)
import cli.template
from ldif import (
    LDIFParser,
)

# example for token auth
# def get_repo_with_token(repo_tag="master"):
#   app_id = env.vars.get("GH_APP_ID")
#   private_key = env.vars.get("GH_PRIVATE_KEY")
#   installation_id = env.vars.get("GH_INSTALLATION_ID")
#   token = git.get_access_token(app_id, private_key, installation_id)


ldap_config = {
    "bind_user": "cn=root,dc=moj,dc=com",
    "bind_user_cn": "root",
    "base_root": "dc=moj,dc=com",
    "base_root_dc": "moj",
    "base_users": "ou=Users,dc=moj,dc=com",
    "base_users_ou": "Users",
    "base_service_users": "cn=EISUsers,ou=Users,dc=moj,dc=com",
    "base_roles": "cn=ndRoleCatalogue,ou=Users,dc=moj,dc=com",
    "base_role_groups": "cn=ndRoleGroups,ou=Users,dc=moj,dc=com",
    "base_groups": "ou=groups,dc=moj,dc=com",
    "base_groups_ou": "groups",
}


def get_repo(
    repo_tag="master",
):
    url = "https://github.com/ministryofjustice/hmpps-ndelius-rbac.git"
    try:
        repo = git.get_repo(
            url,
            dest_name="rbac",
            branch_or_tag=repo_tag,
        )
        return repo
    except Exception as e:
        log.exception(e)
        return None


def prep_for_templating(
    files,
    strings=None,
):
    rbac_substitutions = {
        "bind_password_hash.stdout": "bind_password_hash",
        r"ldap_config.base_users | regex_replace('^.+?=(.+?),.*$', '\\1')": "ldap_config.base_users_ou",
        r"ldap_config.base_root | regex_replace('^.+?=(.+?),.*$', '\\1')": "ldap_config.base_root_dc",
        r"ldap_config.base_groups | regex_replace('^.+?=(.+?),.*$', '\\1')": "ldap_config.base_groups_ou",
        r"ldap_config.bind_user | regex_replace('^.+?=(.+?),.*$', '\\1')": "ldap_config.bind_user_cn",
        "'/'+environment_name+'/'+project_name+'": "",
        "/gdpr/api/": "'gdpr_api_",
        "/pwm/pwm/config_password": "'pwm_config_password",
        "/merge/api/client_secret": "'merge_api_client_secret",
        "/weblogic/ndelius-domain/umt_client_secret": "'umt_client_secret",
        "ssm_prefix + ": "",
        "cn=Users,dc=pcms,dc=internal": "ou=Users,dc=moj,dc=com",
        "ssm_prefix+": "",
    }

    if strings is None:
        strings = env.vars.get("RBAC_SUBSTITUTIONS") or rbac_substitutions

    for file_path in files:
        file = Path(file_path)
        for (
            k,
            v,
        ) in strings.items():
            log.info(f"replacing {k} with {v} in {file_path}")
            file.write_text(
                file.read_text().replace(
                    k,
                    v,
                ),
            )


def template_rbac(
    files,
):
    hashed_pwd_admin_user = ldap3.utils.hashed.hashed(
        ldap3.HASHED_SALTED_SHA,
        env.secrets.get("LDAP_ADMIN_PASSWORD"),
    )
    rendered_files = []

    for file in files:
        rendered_text = cli.template.render(
            file,
            ldap_config=env.vars.get("LDAP_CONFIG") or ldap_config,
            bind_password_hash=hashed_pwd_admin_user,
            secrets=env.secrets,
            oasys_password=env.secrets.get("OASYS_PASSWORD"),
            environment_name=env.vars.get("ENVIRONMENT_NAME"),
            project_name=env.vars.get("PROJECT_NAME"),
        )
        rendered_file = cli.template.save(
            rendered_text,
            file,
        )
        rendered_files.append(rendered_file)
    return rendered_files


def context_ldif(
    rendered_files,
):
    context_file = [file for file in rendered_files if "context" in Path(file).name]
    for file in context_file:
        parser = LDIFParser(
            open(
                file,
                "rb",
            ),
            strict=False,
        )
        for (
            dn,
            record,
        ) in parser.parse():
            log.info(f"got entry record: {dn}")
            log.debug(record)
            try:
                ldap_connection = ldap_connect(
                    env.vars.get("LDAP_HOST"),
                    env.vars.get("LDAP_USER"),
                    env.secrets.get("LDAP_BIND_PASSWORD"),
                )
            except Exception as e:
                log.exception(f"Failed to connect to ldap")
                raise e

            try:
                ldap_connection.add(
                    dn,
                    attributes=record,
                )
                log.debug(ldap_connection.result["result"])
            except Exception as e:
                log.exception(f"Failed to add  {dn}... {record}")
                raise (e)

            if ldap_connection.result["result"] == 0:
                log.info("successfully added context")
            elif ldap_connection.result["result"] == 68:
                log.info(f"{dn} already exists")
            else:
                log.debug(ldap_connection.result)
                log.debug(ldap_connection.response)
                raise Exception(f"Failed to add  {dn}... {record}")


def group_ldifs(
    rendered_files,
):
    # connect to ldap
    try:
        ldap_connection = ldap_connect(
            env.vars.get("LDAP_HOST"),
            env.vars.get("LDAP_USER"),
            env.secrets.get("LDAP_BIND_PASSWORD"),
        )
    except Exception as e:
        log.exception(f"Failed to connect to ldap")
        raise e

    group_files = [file for file in rendered_files if "groups" in Path(file).name]
    # loop through the group files
    for file in group_files:
        # parse the ldif into dn and record
        parser = LDIFParser(
            open(
                file,
                "rb",
            ),
            strict=False,
        )
        # loop through the records
        for (
            dn,
            record,
        ) in parser.parse():
            log.debug(f"got entry record: {dn}")
            log.debug(record)
            # add the record to ldap
            try:
                ldap_connection.add(
                    dn,
                    attributes=record,
                )
            except Exception as e:
                log.exception(f"Failed to add  {dn}... {record}")
                raise (e)

            if record.get("description"):
                log.info(f"Updating description for {record}")
                try:
                    ldap_connection.modify(
                        dn,
                        {
                            "description": [
                                (
                                    ldap3.MODIFY_REPLACE,
                                    record["description"],
                                )
                            ]
                        },
                    )
                except Exception as e:
                    log.exception(f"Failed to add  {dn}... {record}")
                    raise (e)

                if ldap_connection.result["result"] == 0:
                    log.info(f"Successfully added groups")
                elif ldap_connection.result["result"] == 68:
                    log.info(f"{dn} already exists")
                else:
                    log.debug(ldap_connection.result)
                    log.debug(ldap_connection.response)
                    raise Exception(f"Failed to add  {dn}... {record}")


def policy_ldifs(
    rendered_files,
):
    # connect to ldap
    try:
        ldap_connection = ldap_connect(
            env.vars.get("LDAP_HOST"),
            env.vars.get("LDAP_USER"),
            env.secrets.get("LDAP_BIND_PASSWORD"),
        )
    except Exception as e:
        log.exception(f"Failed to connect to ldap")
        raise e

    policy_files = [file for file in rendered_files if "policy" in Path(file).name]

    # first, delete the policies
    ldap_config_dict = env.vars.get("LDAP_CONFIG") or ldap_config
    ldap_connection.delete("ou=Policies," + ldap_config_dict.get("base_root"))

    # loop through the policy files
    for file in policy_files:
        # parse the ldif into dn and record
        parser = LDIFParser(
            open(
                file,
                "rb",
            ),
            strict=False,
        )
        # loop through the records
        for (
            dn,
            record,
        ) in parser.parse():
            log.info(f"got entry record: {dn}")
            # add the record to ldap
            try:
                ldap_connection.add(
                    dn,
                    attributes=record,
                )
            except Exception as e:
                log.exception(f"Failed to add  {dn}... {record}")
                raise (e)

            if ldap_connection.result["result"] == 0:
                log.info(f"Successfully added policies")
            elif ldap_connection.result["result"] == 68:
                log.info(f"{dn} already exists")
            else:
                log.debug(ldap_connection.result)
                log.debug(ldap_connection.response)
                raise Exception(f"Failed to add  {dn}... {record}")


def role_ldifs(
    rendered_files,
):
    # connect to ldap
    try:
        ldap_connection = ldap_connect(
            env.vars.get("LDAP_HOST"),
            env.vars.get("LDAP_USER"),
            env.secrets.get("LDAP_BIND_PASSWORD"),
        )
    except Exception as e:
        log.exception(f"Failed to connect to ldap")
        raise e
    role_files = [file for file in rendered_files if "nd_role" in Path(file).name]

    # first, delete the roles
    ldap_config_dict = env.vars.get("LDAP_CONFIG") or ldap_config
    ldap_connection.delete("cn=ndRoleCatalogue," + ldap_config_dict.get("base_users"))
    ldap_connection.delete("cn=ndRoleGroups," + ldap_config_dict.get("base_users"))

    # ensure boolean values are Uppercase.. this comes from the ansible yml
    # (not yet implemented, probably not needed)

    # loop through the role files
    for file in role_files:
        # parse the ldif into dn and record
        parser = LDIFParser(
            open(
                file,
                "rb",
            ),
            strict=False,
        )
        # loop through the records
        for (
            dn,
            record,
        ) in parser.parse():
            log.info(f"got entry record: {dn}")
            # add the record to ldap
            try:
                ldap_connection.add(
                    dn,
                    attributes=record,
                )
            except Exception as e:
                log.exception(f"Failed to add  {dn}... {record}")
                raise (e)

            if ldap_connection.result["result"] == 0:
                log.info(f"Successfully added roles")
            elif ldap_connection.result["result"] == 68:
                log.info(f"{dn} already exists")
            else:
                log.debug(ldap_connection.result)
                log.debug(ldap_connection.response)
                raise Exception(f"Failed to add  {dn}... {record}")


# not complete!!
# see https://github.com/ministryofjustice/hmpps-delius-pipelines/blob/master/components/delius-core/playbooks/rbac/import_schemas.yml
def schema_ldifs(
    rendered_files,
):
    # connect to ldap
    try:
        ldap_connection = ldap_connect(
            env.vars.get("LDAP_HOST"),
            env.vars.get("LDAP_USER"),
            env.secrets.get("LDAP_BIND_PASSWORD"),
        )
    except Exception as e:
        log.exception(f"Failed to connect to ldap")
        raise e

    schema_files = [
        file
        for file in rendered_files
        if "delius.ldif" or "pwm.ldif" in Path(file).name
    ]

    # loop through the schema files
    for file in schema_files:
        # parse the ldif into dn and record
        parser = LDIFParser(
            open(
                file,
                "rb",
            ),
            strict=False,
        )
        # loop through the records
        for (
            dn,
            record,
        ) in parser.parse():
            log.info(f"got entry record: {dn}")
            # add the record to ldap
            try:
                ldap_connection.add(
                    dn,
                    attributes=record,
                )
            except Exception as e:
                log.exception(f"Failed to add  {dn}... {record}")
                raise (e)

            if ldap_connection.result["result"] == 0:
                log.info(f"Successfully added schemas")
            elif ldap_connection.result["result"] == 68:
                log.info(f"{dn} already exists")
            else:
                log.debug(ldap_connection.result)
                log.debug(ldap_connection.response)
                raise Exception(f"Failed to add  {dn}... {record}")


def user_ldifs(
    rendered_files,
):
    # connect to ldap
    try:
        ldap_connection = ldap_connect(
            env.vars.get("LDAP_HOST"),
            env.vars.get("LDAP_USER"),
            env.secrets.get("LDAP_BIND_PASSWORD"),
        )
    except Exception as e:
        log.exception(f"Failed to connect to ldap")
        raise (e)

    user_files = [file for file in rendered_files if "-users" in Path(file).name]

    # first, delete the users
    for file in user_files:
        # parse the ldif into dn and record
        parser = LDIFParser(
            open(
                file,
                "rb",
            ),
            strict=False,
        )
        # loop through the records
        for (dn,) in parser.parse():
            log.info(f"got entry record: {dn}")

            # for each user find child entries
            try:
                ldap_connection.search(
                    dn,
                    "(objectclass=*)",
                    search_scope=ldap3.SUBTREE,
                )
            except Exception as e:
                log.exception(f"Failed to search {dn}")
                raise (e)

            #  delete child entries
            try:
                for entry in ldap_connection.entries:
                    log.debug(entry.entry_dn)
                    ldap_connection.delete(entry.entry_dn)
            except Exception as e:
                log.exception(f"Failed to delete {entry.entry_dn}")
                raise (e)

            try:
                ldap_connection.delete(dn)
            except Exception as e:
                log.exception(f"Failed to delete {dn}")
                raise (e)

    # loop through the user files
    for file in user_files:
        # parse the ldif into dn and record
        parser = LDIFParser(
            open(
                file,
                "rb",
            ),
            strict=False,
        )
        # loop through the records
        for (
            dn,
            record,
        ) in parser.parse():
            log.info(f"got entry record: {dn}")

            # add the record to ldap
            try:
                ldap_connection.add(
                    dn,
                    attributes=record,
                )
            except Exception as e:
                log.exception(f"Failed to add  {dn}... {record}")
                raise (e)

            if ldap_connection.result["result"] == 0:
                log.info(f"Successfully added users")
            elif ldap_connection.result["result"] == 68:
                log.info(f"{dn} already exists")
            else:
                log.debug(ldap_connection.result)
                log.debug(ldap_connection.response)
                raise Exception(f"Failed to add  {dn}... {record}")


def main(
    rbac_repo_tag,
    clone_path="./rbac",
):
    get_repo(rbac_repo_tag)
    files = [
        file
        for file in glob.glob(
            f"{clone_path}/**/*",
            recursive=True,
        )
        if Path(file).is_file()
        and Path(file).name.endswith(".ldif")
        or Path(file).name.endswith(".j2")
    ]

    prep_for_templating(files)
    rendered_files = template_rbac(files)
    context_ldif(rendered_files)
    policy_ldifs(rendered_files)
    # schema_ldifs(files) probably not needed, but need to check!
    role_ldifs(rendered_files)
    group_ldifs(rendered_files)
    user_ldifs(rendered_files)
