import oracledb
import os
from cli import (
    env,
)
from cli.logger import (
    log,
)


def initialize_oracle_client():
    lib_dir = os.environ.get("ORACLE_CLIENT_PATH")

    if not lib_dir:
        log.debug("Error: ORACLE_CLIENT_PATH environment variable is not set.")
        raise EnvironmentError("ORACLE_CLIENT_PATH is not set.")

    if not os.path.isdir(lib_dir):
        log.debug(f"Error: Oracle client directory does not exist: {lib_dir}")
        raise FileNotFoundError(f"Oracle client path does not exist: {lib_dir}")

    try:
        oracledb.init_oracle_client(lib_dir=lib_dir)
        log.debug("Oracle client initialized successfully.")
    except Exception as e:
        log.exception(f"Error initializing Oracle client: {e}")
        raise e


def connection():
    initialize_oracle_client()
    try:
        conn = oracledb.connect(env.secrets.get("DB_CONNECTION_STRING"))
        log.debug("Created database connection successfully")
        return conn
    except Exception as e:
        log.exception(
            f"Failed to create database connection. An exception of type {type(e).__name__} occurred: {e}"
        )
        raise e
