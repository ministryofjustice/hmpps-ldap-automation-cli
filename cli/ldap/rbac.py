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


def prep_for_templating(dir, strings=None):
    if strings is None:
        strings = env.vars.get("RBAC_SUBSTITUTIONS")
    # get a list of files
    print(type(strings))
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
