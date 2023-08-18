from github import Github, Auth
from git import Repo
import jwt
import time
import requests
import logging
from cli import config
def get_access_token(app_id, private_key, installation_id):
    # Create a JSON Web Token (JWT) using the app's private key
    now = int(time.time())
    payload = {
        "iat": now,
        "exp": now + 600,
        "iss": app_id
    }
    jwt_token = jwt.encode(payload, private_key, algorithm="RS256")

    # Exchange the JWT for an installation access token
    headers = {
        "Authorization": f"Bearer {jwt_token}",
        "Accept": "application/vnd.github.v3+json"
    }
    response = requests.post(f"https://api.github.com/app/installations/{installation_id}/access_tokens",
                             headers=headers)
    # extract the token from the response
    access_token = response.json().get("token")
    return access_token

def get_repo(url, token=None, auth_type="x-access-token", dest_name="repo"):
    # if there is an @ in the url, assume auth is already specified
    if '@' in url:
        logging.info('auth already specified in url')
        return Repo.clone_from(url, dest_name)
    # if there is a token, assume auth is required and use the token and auth_type
    elif token:
        templated_url = f'https://{auth_type}:{token}@{url.split("//")[1]}'
        logging.info(f'cloning with token: {templated_url}')
        return Repo.clone_from(templated_url, dest_name)
    # if there is no token, assume auth is not required and clone without
    else:
        logging.info('cloning without auth')
        return Repo.clone_from(url, dest_name)
def dl_test():
    app_id = config.gh_app_id
    private_key = config.gh_private_key
    installation_id = config.gh_installation_id
    url = 'https://github.com/ministryofjustice/hmpps-delius-pipelines.git'
    token = get_access_token(app_id, private_key, installation_id)
    repo = get_repo(url, token=token, dest_name='delius-pipelines')
    print(repo)