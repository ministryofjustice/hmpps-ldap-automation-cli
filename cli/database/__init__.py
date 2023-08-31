import oracledb
import cli.env
from logger import log

connection_config = {
    "user": cli.env.vars.get("DB_USER"),
    "password": cli.env.secrets.get("DB_PASSWORD"),
    "dsn": cli.env.vars.get("DB_DSN"),
}


def connection():
    try:
        conn = oracledb.connect(**connection_config)
        log.debug("Created database connection successfully")
        return conn
    except Exception as e:
        log.exception(e)
        raise e
