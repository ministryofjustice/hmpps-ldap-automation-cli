import oracledb
from cli import (
    env,
)
from cli.logger import (
    log,
)


def connection():
    try:
        conn = oracledb.connect(env.secrets.get("DB_CONNECTION_STRING"))
        log.debug("Created database connection successfully")
        return conn
    except Exception as e:
        log.exception(
            f"Failed to create database connection. An exception of type {type(e).__name__} occurred: {e}"
        )
        raise e
