import glob
from pathlib import (
    Path,
)
from pprint import pprint

import ldap
import ldap.modlist as modlist
import ldap3.utils.hashed
import ldif

import cli.git as git
import cli.template
from cli import (
    env,
)
from cli.logger import (
    log,
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
        log.info("Replacing strings in rbac files")
        for (
            k,
            v,
        ) in strings.items():
            log.debug(f"replacing {k} with {v} in {file_path}")
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

    # connect to ldap
    try:
        log.info("Connecting to ldap")
        log.info(
            f"ldap://{env.vars.get('LDAP_HOST')}:{env.vars.get('LDAP_PORT', '389')}"
        )
        connection = ldap.initialize(
            f"ldap://{env.vars.get('LDAP_HOST')}:{env.vars.get('LDAP_PORT', '389')}"
        )
        connection.simple_bind_s(
            env.vars.get("LDAP_USER"), env.secrets.get("LDAP_BIND_PASSWORD")
        )
    except Exception as e:
        log.exception("Failed to connect to ldap")
        raise e

    for file in context_file:
        # parse the ldif into dn and record

        records = ldif.LDIFRecordList(open(file, "rb"))
        records.parse()

        pprint(records.all_records)
        # loop through the records
        for entry in records.all_records:
            dn = entry[0]
            attributes = entry[1]
            log.info(f"got entry record: {dn}")
            log.debug(attributes)
            try:
                connection.add_s(
                    dn,
                    modlist.addModlist(attributes),
                )
                log.info(f"{dn} Added")
            except ldap.ALREADY_EXISTS as already_exists_e:
                log.info(f"{dn} already exists")
                log.debug(already_exists_e)
            except Exception as e:
                log.exception(f"Failed to add  {dn}... {attributes}")
                raise e


def group_ldifs(
    rendered_files,
):
    # connect to ldap
    try:
        connection = ldap.initialize(
            f"ldap://{env.vars.get('LDAP_HOST')}:{env.vars.get('LDAP_PORT', '389')}"
        )
        connection.simple_bind_s(
            env.vars.get("LDAP_USER"), env.secrets.get("LDAP_BIND_PASSWORD")
        )
    except Exception as e:
        log.exception("Failed to connect to ldap")
        raise e

    group_files = [file for file in rendered_files if "-groups" in Path(file).name]
    # loop through the group files
    for file in group_files:
        # parse the ldif into dn and record

        records = ldif.LDIFRecordList(open(file, "rb"))
        records.parse()

        pprint(records.all_records)
        # loop through the records
        for entry in records.all_records:
            dn = entry[0]
            attributes = entry[1]
            log.debug(f"got entry record: {dn}")
            log.debug(attributes)
            # add the record to ldap
            try:
                connection.add_s(
                    dn,
                    modlist.addModlist(attributes),
                )
                log.info(f"{dn} Added")
            except ldap.ALREADY_EXISTS as already_exists_e:
                log.info(f"{dn} already exists")
                log.debug(already_exists_e)
            except Exception as e:
                log.exception(f"Failed to add  {dn}... {attributes}")
                raise e

            if attributes.get("description"):
                log.info(f"Updating description for {dn}")
                try:
                    connection.modify(
                        dn,
                        [
                            (
                                ldap.MOD_REPLACE,
                                "description",
                                attributes["description"],
                            )
                        ],
                    )
                except ldap.ALREADY_EXISTS as already_exists_e:
                    log.info(f"{dn} already exists")
                    log.debug(already_exists_e)
                except Exception as e:
                    log.exception(f"Failed to add  {dn}... {attributes}")
                    raise e


def policy_ldifs(
    rendered_files,
):
    # connect to ldap
    try:
        connection = ldap.initialize(
            f"ldap://{env.vars.get('LDAP_HOST')}:{env.vars.get('LDAP_PORT', '389')}"
        )
        connection.simple_bind_s(
            env.vars.get("LDAP_USER"), env.secrets.get("LDAP_BIND_PASSWORD")
        )
    except Exception as e:
        log.exception("Failed to connect to ldap")
        raise e

    log.debug("*********************************")
    log.debug("STARTING POLICY LDIFS")
    log.debug("*********************************")

    policy_files = [file for file in rendered_files if "policy" in Path(file).name]

    # first, delete the policies
    ldap_config_dict = env.vars.get("LDAP_CONFIG") or ldap_config
    policy_tree = f"ou=Policies,{ldap_config_dict.get('base_root')}"

    log.debug(f"Policy tree: {policy_tree}")

    try:
        tree = connection.search_s(
            policy_tree,
            ldap.SCOPE_SUBTREE,
            "(objectClass=*)",
        )
        tree.reverse()
    except ldap.NO_SUCH_OBJECT:
        log.debug("Entire policy ou does not exist, no need to delete child objects")
        tree = None

    log.debug("*********************************")
    log.debug("DELETING POLICY ENTRIES")
    log.debug("*********************************")

    if tree is not None:
        for entry in tree:
            try:
                log.debug(entry[0])
                connection.delete_ext_s(
                    entry[0],
                    serverctrls=[ldap.controls.simple.ManageDSAITControl()],
                )
                print(f"Deleted {entry[0]}")
            except ldap.NO_SUCH_OBJECT as no_such_object_e:
                log.debug(f"this is the entry {entry}")
                log.debug("error deleting entry")
                log.info("No such object found, 32")
                log.debug(no_such_object_e)

    log.debug("*********************************")
    log.debug("RECREATING POLICY ENTRIES")
    log.debug("*********************************")
    # loop through the policy files
    for file in policy_files:
        # parse the ldif into dn and record
        #
        log.debug(f"Reading file {file}")

        records = ldif.LDIFRecordList(open(file, "rb"))
        records.parse()

        pprint(records.all_records)
        # loop through the records
        for entry in records.all_records:
            dn = entry[0]
            attributes = entry[1]
            log.info(f"Got entry record: {dn}")
            # add the record to ldap
            try:
                connection.add_s(
                    dn,
                    modlist.addModlist(attributes),
                )
                log.info(f"{dn} Added")
            except ldap.ALREADY_EXISTS as already_exists_e:
                log.info(f"{dn} already exists")
                log.debug(already_exists_e)
            except Exception as e:
                log.exception(f"Failed to add  {dn}... {attributes}")
                raise e
    log.debug("*********************************")
    log.debug("FINISHED POLICY LDIFS")
    log.debug("*********************************")


def role_ldifs(
    rendered_files,
):
    # connect to ldap
    try:
        connection = ldap.initialize(
            f"ldap://{env.vars.get('LDAP_HOST')}:{env.vars.get('LDAP_PORT', '389')}"
        )
        connection.simple_bind_s(
            env.vars.get("LDAP_USER"), env.secrets.get("LDAP_BIND_PASSWORD")
        )
    except Exception as e:
        log.exception("Failed to connect to ldap")
        raise e

    log.debug("*********************************")
    log.debug("STARTING ROLES")
    log.debug("*********************************")

    role_files = [file for file in rendered_files if "nd_role" in Path(file).name]

    # first, delete the roles
    ldap_config_dict = env.vars.get("LDAP_CONFIG") or ldap_config

    role_trees = [
        "cn=ndRoleCatalogue," + ldap_config_dict.get("base_users"),
        "cn=ndRoleGroups," + ldap_config_dict.get("base_users"),
    ]

    for role_tree in role_trees:
        try:
            tree = connection.search_s(
                role_tree,
                ldap.SCOPE_SUBTREE,
                "(objectClass=*)",
            )
            tree.reverse()
        except ldap.NO_SUCH_OBJECT:
            log.debug("Entire role ou does not exist, no need to delete child objects")
            tree = None
        log.debug("*********************************")
        log.debug("DELETING ROLES")
        log.debug("*********************************")
        if tree is not None:
            for entry in tree:
                try:
                    log.debug(entry[0])
                    connection.delete_ext_s(
                        entry[0],
                        serverctrls=[ldap.controls.simple.ManageDSAITControl()],
                    )
                    print(f"Deleted {entry[0]}")
                except ldap.NO_SUCH_OBJECT as no_such_object_e:
                    log.info("No such object found, 32")
                    log.debug(no_such_object_e)

    # ensure boolean values are Uppercase.. this comes from the ansible yml
    # (not yet implemented, probably not needed)
    log.debug("*********************************")
    log.debug("RECREATING ROLES")
    log.debug("*********************************")
    # loop through the role files
    for file in role_files:
        # parse the ldif into dn and record

        records = ldif.LDIFRecordList(open(file, "rb"))
        records.parse()

        pprint(records.all_records)
        # loop through the records
        for entry in records.all_records:
            dn = entry[0]
            attributes = entry[1]
            log.info(f"Got entry record: {dn}")
            # add the record to ldap
            try:
                connection.add_s(
                    dn,
                    modlist.addModlist(attributes),
                )
                log.info(f"{dn} Added")
            except ldap.ALREADY_EXISTS as already_exists_e:
                log.info(f"{dn} already exists")
                log.debug(already_exists_e)
            except Exception as e:
                log.exception(f"Failed to add  {dn}... {attributes}")
                raise e
    log.debug("*********************************")
    log.debug("FINISHED ROLES")
    log.debug("*********************************")


# not complete!!
# see https://github.com/ministryofjustice/hmpps-delius-pipelines/blob/master/components/delius-core/playbooks/rbac/import_schemas.yml
def schema_ldifs(
    rendered_files,
):
    # connect to ldap
    try:
        connection = ldap.initialize(
            f"ldap://{env.vars.get('LDAP_HOST')}:{env.vars.get('LDAP_PORT', '389')}"
        )
        connection.simple_bind_s(
            env.vars.get("LDAP_USER"), env.secrets.get("LDAP_BIND_PASSWORD")
        )
    except Exception as e:
        log.exception("Failed to connect to ldap")
        raise e

    schema_files = [
        file
        for file in rendered_files
        if "delius.ldif" or "pwm.ldif" in Path(file).name
    ]

    # loop through the schema files
    for file in schema_files:
        # parse the ldif into dn and record
        records = ldif.LDIFRecordList(open(file, "rb"))
        records.parse()
        # loop through the records
        for entry in records.all_records:
            log.info(f"Got entry record: {dn}")
            # add the record to ldap
            try:
                dn = entry[0]
                attributes = entry[1]
                print(f" {entry[0]}")
                connection.add_s(dn, modlist.addModlist(attributes))
                log.info(f"{dn} Added")
            except ldap.ALREADY_EXISTS as already_exists_e:
                log.info(f"{dn} already exists")
                log.debug(already_exists_e)
            except Exception as e:
                log.exception(f"Failed to add  {dn}... {attributes}")
                raise e


def user_ldifs(
    rendered_files,
):
    # connect to ldap
    try:
        connection = ldap.initialize(
            f"ldap://{env.vars.get('LDAP_HOST')}:{env.vars.get('LDAP_PORT', '389')}"
        )
        connection.simple_bind_s(
            env.vars.get("LDAP_USER"), env.secrets.get("LDAP_BIND_PASSWORD")
        )
    except Exception as e:
        log.exception("Failed to connect to ldap")
        raise e

    except Exception as e:
        log.exception("Failed to connect to ldap")
        raise e

    user_files = [file for file in rendered_files if "-users.ldif" in Path(file).name]

    # first, delete the users
    for file in user_files:
        records = ldif.LDIFRecordList(open(file, "rb"))
        records.parse()

        for record in records.all_records:
            dn = record[0]
            log.info(f"Got entry record: {dn}")
            try:
                # search for dn children
                tree = connection.search_s(
                    dn,
                    ldap.SCOPE_SUBTREE,
                    "(objectClass=*)",
                )
                tree.reverse()

                for entry in tree:
                    try:
                        log.debug(entry[0])
                        connection.delete_ext_s(
                            entry[0],
                            serverctrls=[ldap.controls.simple.ManageDSAITControl()],
                        )
                        print(f"Deleted {entry[0]}")
                    except ldap.NO_SUCH_OBJECT as no_such_object_e:
                        log.info("No such object found, 32")
                        log.debug(no_such_object_e)
                # connection.delete_ext_s(dn, serverctrls=[ldap.controls.simple.ManageDSAITControl()])
                # print(f"Deleted {dn}")
            except ldap.NO_SUCH_OBJECT as no_such_object_e:
                log.info("No such object found, 32")
                log.debug(no_such_object_e)
            except Exception as e:
                log.exception(e)
                raise e

    for file in user_files:
        records = ldif.LDIFRecordList(open(file, "rb"))
        records.parse()

        # pprint(records.all_records)
        # loop through the records
        for entry in records.all_records:
            log.info(f"Got entry record: {dn}")
            try:
                dn = entry[0]
                attributes = entry[1]
                print(f" {entry[0]}")
                connection.add_s(dn, modlist.addModlist(attributes))
                log.info(f"{dn} Added")
            except ldap.ALREADY_EXISTS as already_exists_e:
                log.info(f"{dn} already exists")
                log.debug(already_exists_e)

    # connect to ldap
    # try:
    #     ldap_connection_addition = ldap_connect(
    #         env.vars.get("LDAP_HOST"),
    #         env.vars.get("LDAP_USER"),
    #         env.secrets.get("LDAP_BIND_PASSWORD"),
    #     )
    # except Exception as e:
    #     log.exception(f"Failed to connect to ldap")
    #     raise e

    # loop through the user files
    # for file in user_files:
    #     # parse the ldif into dn and record
    #     parser = LDIFParser(
    #         open(
    #             file,
    #             "rb",
    #         ),
    #         strict=False,
    #     )
    #     # loop through the records
    #     for (
    #         dn,
    #         record,
    #     ) in parser.parse():
    #         log.info(f"Got entry record: {dn}")
    #
    #         # add the record to ldap
    #         try:
    #             print(dn)
    #             print(record)
    #             ldap_connection_addition.add(
    #                 dn,
    #                 record,
    #             )
    #         except Exception as e:
    #             log.exception(f"Failed to add  {dn}... {record}")
    #             raise e
    #
    #         if ldap_connection_addition.result["result"] == 0:
    #             log.info(f"Successfully added users")
    #         elif ldap_connection_addition.result["result"] == 68:
    #             log.info(f"{dn} already exists")
    #         else:
    #             log.debug(ldap_connection_addition.result)
    #             log.debug(ldap_connection_addition.response)
    #             raise Exception(f"Failed to add  {dn}... {record}")


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
