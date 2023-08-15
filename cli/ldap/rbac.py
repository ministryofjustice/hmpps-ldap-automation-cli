from cli import env
import cli.git as git
import logging
import glob
from logging import log


def get_repo():
    app_id = env.vars.get("GH_APP_ID")
    private_key = env.vars.get("GH_PRIVATE_KEY")
    installation_id = env.vars.get("GH_INSTALLATION_ID")
    # url = 'https://github.com/ministryofjustice/hmpps-delius-pipelines.git'
    url = 'https://github.com/ministryofjustice/hmpps-ndelius-rbac.git'
    token = git.get_access_token(app_id, private_key, installation_id)
    try:
        repo = git.get_repo(url, token=token, dest_name='rbac')
        return repo
    except Exception as e:
        logging.exception(e)
        return None


def prep_for_templating(dir):
    # get a list of files
    files = glob.glob(f'{dir}/**/*', recursive=True)
