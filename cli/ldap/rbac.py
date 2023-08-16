import re

import ldap3.utils.hashed

from cli import env
import cli.git as git
import glob
from cli.logging import log
from pathlib import Path
import cli.template


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


def prep_for_templating(dir, strings=None):
    if strings is None:
        strings = env.vars.get("RBAC_SUBSTITUTIONS")
    # get a list of files
    # print(strings)
    # print(type(strings))
    files = [
        file
        for file in glob.glob(f"{dir}/**/*", recursive=True)
        if Path(file).is_file() and Path(file).name.endswith("ldif.j2")
    ]
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


def test():
    repo = get_repo()
    print(env.vars.get("RBAC_SUBSTITUTIONS"))
    dir = "./rbac"
    prep_for_templating(dir)
    hashed_pwd_admin_user = ldap3.utils.hashed.hashed(ldap3.HASHED_SALTED_SHA, env.secrets.get("LDAP_ADMIN_PASSWORD"))
    files = [
        file
        for file in glob.glob(f"{dir}/**/*", recursive=True)
        if Path(file).is_file() and Path(file).name.endswith(".ldif.j2")
    ]
    # print(files)
    for file in files:
        rendered_text = cli.template.render(
            file,
            ldap_config=env.vars.get("LDAP_CONFIG"),
            bind_password_hash=hashed_pwd_admin_user,
            secrets=env.secrets,
            oasys_password=env.secrets.get("OASYS_PASSWORD"),
            environment_name=env.vars.get("ENVIRONMENT_NAME"),
            project_name=env.vars.get("PROJECT_NAME"),
        )
        cli.template.save(rendered_text, file)
