from cli import env
import cli.git as git
import logging
import glob


def get_repo():
    app_id = config.gh_app_id
    private_key = config.gh_private_key
    installation_id = config.gh_installation_id
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
