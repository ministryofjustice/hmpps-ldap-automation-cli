import os

from dotenv import (
    dotenv_values,
)

import ast

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
    **{
        key.replace(
            "VAR_",
            "",
        ).replace(
            "_DICT",
            "",
        ): ast.literal_eval(val)
        if "DICT" in key
        else val
        for key, val in dotenv_values(".vars").items()
        if val is not None
    },  # load development variables
    **{
        key.replace(
            "VAR_",
            "",
        ).replace(
            "_DICT",
            "",
        ): ast.literal_eval(val)
        if "DICT" in key
        else val
        for key, val in os.environ.items()
        if key.startswith("VAR_") and val is not None
    },
}
# loads all environment variables starting with SECRET_ into a dictionary
secrets = {
    **{
        key.replace(
            "SECRET_",
            "",
        )
        .replace(
            "_DICT",
            "",
        )
        .replace(
            "SSM_",
            "",
        ): ast.literal_eval(val)
        if "_DICT" in key
        else val
        for key, val in dotenv_values(".secrets").items()
        if val is not None
    },
    **{
        key.replace(
            "SECRET_",
            "",
        )
        .replace(
            "_DICT",
            "",
        )
        .replace(
            "SSM_",
            "",
        ): ast.literal_eval(val)
        if "DICT" in key
        else val
        for key, val in os.environ.items()
        if key.startswith("SECRET_") or key.startswith("SSM_") and val is not None
    },
}
