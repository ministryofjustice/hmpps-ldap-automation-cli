import oracledb
from cli import env
from cli.logger import log

connection_config = {
    "user": env.vars.get("DB_USER"),
    "password": env.secrets.get("DB_PASSWORD"),
    "dsn": env.vars.get("DB_DSN"),
}


def connection():
    try:
        conn = oracledb.connect(**connection_config)
        log.debug("Created database connection successfully")
        return conn
    except Exception as e:
        log.exception(e)
        raise e
