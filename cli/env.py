import os

from dotenv import dotenv_values

# ldap_host = os.getenv("LDAP_HOST")
# ldap_user = os.getenv("LDAP_USER")
# ldap_password = os.getenv("LDAP_PASSWORD")
# db_user = os.getenv("DB_USER")
# db_password = os.getenv("DB_PASSWORD")
# db_host = os.getenv("DB_HOST")
# db_port = os.getenv("DB_PORT")
# db_service_name = os.getenv("DB_SERVICE_NAME")
# gh_app_id = os.getenv("GH_APP_ID")
# gh_private_key = os.getenv("GH_PRIVATE_KEY")
# gh_installation_id = os.getenv("GH_INSTALLATION_ID")

vars = {
    **dotenv_values(".env"),  # load development variables
    **{key: val for key, val in os.environ.items() if key.startswith(('LDAP_', 'DB_', 'GH_'))}
    # load all other environment variables starting with LDAP_, DB_, GH_
}
print(vars)
# loads all environment variables starting with SECRET_ into a dictionary
secrets = {key.replace("SECRET_"): val for key, val in os.environ.items() if key.startswith("SECRET_")}
