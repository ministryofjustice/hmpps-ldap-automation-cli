import oracledb
from cli import env
from cli.logger import log


def connection():
    try:
        conn = oracledb.connect(env.secrets.get("DB_CONNECTION_STRING"))
        log.debug("Created database connection successfully")
        return conn
    except Exception as e:
        log.exception(e)
        raise e
