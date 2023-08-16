import re

from cli import env
import cli.git as git
import glob
from cli.logging import log
from pathlib import Path


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


def prep_for_templating(dir):
    strings = {
        r"ldap_config.base_users | regex_replace('^.+?=(.+?),.*$', '\\1')": "ldap_config.base_users_ou",
        r"ldap_config.base_root | regex_replace('^.+?=(.+?),.*$', '\\1')": "ldap_config.root_ou",
        r"ldap_config.base_groups | regex_replace('^.+?=(.+?),.*$', '\\1')": "ldap_config.base_groups_ou",
        r"ldap_config.bind_user | regex_replace('^.+?=(.+?),.*$', '\\1')": "ldap_config.bind_user_ou",
    }
    # get a list of files
    files = [
        file
        for file in glob.glob(f"{dir}/**/*", recursive=True)
        if Path(file).is_file() and Path(file).name.endswith(".j2")
    ]
    for file_path in files:
        file = Path(file_path)
        for k, v in strings.items():
            print(file.read_text())
            file.write_text(
                file.read_text().replace(k, v),
            )


def test():
    repo = get_repo()

    prep_for_templating(repo.working_dir)
