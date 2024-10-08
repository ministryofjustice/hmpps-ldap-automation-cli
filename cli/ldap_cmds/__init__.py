from ldap3 import (
    Server,
    Connection,
)


# import oracledb
def ldap_connect(ldap_host, ldap_port, ldap_user, ldap_password):
    server = Server(ldap_host, ldap_port)

    return Connection(
        server=server,
        user=ldap_user,
        password=ldap_password,
        auto_bind="NO_TLS",
        authentication="SIMPLE",
    )


# def db_connect(db_user, db_password, db_host, db_port, db_service_name):
#     return oracledb.connect(db_user, db_password, db_host, db_port, db_service_name)


# def db_command(db_command, db_connection=None):
#     db_connection = db_connect() if not db_connection else db_connection
#     with db_connection:
#         return db_connection.cursor().execute(db_command)
