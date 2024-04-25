import oracledb

import cli.ldap_cmds

from cli.logger import (
    log,
)
from cli import (
    env,
)

from cli.ldap_cmds import (
    ldap_connect,
)
from ldap3 import (
    MODIFY_REPLACE,
    MODIFY_DELETE,
    DEREF_NEVER,
)

import cli.database
from itertools import (
    product,
)

from datetime import (
    datetime,
)


#########################################
# Change a users home area
#########################################
def change_home_areas(
    old_home_area,
    new_home_area,
    user_ou,
    root_dn,
    attribute="userHomeArea",
    object_class="NDUser",
):
    log.info(f"Updating user home areas from {old_home_area} to {new_home_area}")
    ldap_connection = ldap_connect(
        env.vars.get("LDAP_HOST"),
        env.vars.get("LDAP_USER"),
        env.secrets.get("LDAP_BIND_PASSWORD"),
    )

    search_filter = (
        f"(&(objectclass={object_class})(userHomeArea={old_home_area})(!(cn={old_home_area}))(!(endDate=*)))"
    )
    ldap_connection.search(
        ",".join(
            [
                user_ou,
                root_dn,
            ]
        ),
        search_filter,
        attributes=[attribute],
    )

    # Iterate through the search results and update the attribute
    for entry in ldap_connection.entries:
        dn = entry.entry_dn
        changes = {
            attribute: [
                (
                    MODIFY_REPLACE,
                    [new_home_area],
                )
            ]
        }
        ldap_connection.modify(
            dn,
            changes,
        )

        # Check if the modification was successful
        if ldap_connection.result["result"] == 0:
            log.info(f"Successfully updated {attribute} for {dn}")
        else:
            log.error(f"Failed to update {attribute} for {dn}: {ldap_connection.result}")


#########################################
#  Add roles to a user
#########################################


def parse_user_role_list(
    user_role_list,
):
    # The format of the list should be a pipe separated list of username and role lists,
    # where the username and role list is separated by a comma character,
    # and the roles are separated by a semi-colon:
    # username1,role1;role2;role3|username2,role1;role2

    return {user.split(",")[0]: user.split(",")[1].split(";") for user in user_role_list.split("|")}


def add_roles_to_user(
    username,
    roles,
    user_ou="ou=Users",
    root_dn="dc=moj,dc=com",
):
    log.info(f"Adding roles {roles} to user {username}")
    ldap_connection = ldap_connect(
        env.vars.get("LDAP_HOST"),
        env.vars.get("LDAP_USER"),
        env.secrets.get("LDAP_BIND_PASSWORD"),
    )
    for role in roles:
        try:
            ldap_connection.add(
                f"cn={role},cn={username},{user_ou},{root_dn}",
                attributes={
                    "objectClass": [
                        "NDRoleAssociation",
                        "alias",
                    ],
                    "aliasedObjectName": f"cn={role},cn={username},cn=ndRoleCatalogue,{user_ou},{root_dn}",
                },
            )
        except Exception as e:
            log.exception(f"Failed to add role {role} to user {username}")
            raise e

        if ldap_connection.result["result"] == 0:
            log.info(f"Successfully added role {role} to user {username}")
        elif ldap_connection.result["result"] == 68:
            log.info(f"Role {role} already exists for user {username}")
        else:
            log.debug(ldap_connection.result)
            log.debug(ldap_connection.response)
            raise Exception(f"Failed to add role {role} to user {username}")


def process_user_roles_list(
    user_role_list,
    user_ou="ou=Users",
    root_dn="dc=moj,dc=com",
):
    user_roles = parse_user_role_list(user_role_list)
    try:
        for (
            user,
            roles,
        ) in user_roles.items():
            add_roles_to_user(
                user,
                roles,
                user_ou,
                root_dn,
            )
    except Exception as e:
        log.exception(f"Failed to add role to user")
        raise e


#########################################
#  Update user roles
#########################################


def update_roles(
    roles,
    user_ou,
    root_dn,
    add,
    remove,
    update_notes,
    user_note,
    user_filter="(userSector=*)",
    role_filter="*",
):
    if update_notes and (user_note is None or len(user_note) < 1):
        log.error("User note must be provided when updating notes")
        raise Exception("User note must be provided when updating notes")

    try:
        ldap_connection_user_filter = ldap_connect(
            env.vars.get("LDAP_HOST"),
            env.vars.get("LDAP_USER"),
            env.secrets.get("LDAP_BIND_PASSWORD"),
        )
    except Exception as e:
        log.exception("Failed to connect to LDAP")
        raise e

    # # Search for users matching the user_filter
    try:
        ldap_connection_user_filter.search(
            ",".join(
                [
                    user_ou,
                    root_dn,
                ]
            ),
            user_filter,
            attributes=["cn"],
        )
    except Exception as e:
        log.exception("Failed to search for users")
        raise e

    users_found = sorted([entry.cn.value for entry in ldap_connection_user_filter.entries if entry.cn.value])
    log.debug("users found from user filter")
    log.debug(users_found)
    ldap_connection_user_filter.unbind()

    roles_filter_list = role_filter.split(",")
    roles = roles.split(",")

    # create role filter
    if len(roles_filter_list) > 0:
        full_role_filter = (
            f"(&(objectclass=NDRoleAssociation)(|{''.join(['(cn=' + role + ')' for role in roles_filter_list])}))"
        )
    else:
        full_role_filter = "(&(objectclass=NDRoleAssociation)(cn=*))"

    # Search for roles matching the role_filter

    try:
        ldap_connection_role_filter = ldap_connect(
            env.vars.get("LDAP_HOST"),
            env.vars.get("LDAP_USER"),
            env.secrets.get("LDAP_BIND_PASSWORD"),
        )
    except Exception as e:
        log.exception("Failed to connect to LDAP")
        raise e

    try:
        ldap_connection_role_filter.search(
            ",".join(
                [
                    user_ou,
                    root_dn,
                ]
            ),
            full_role_filter,
            attributes=["cn"],
            dereference_aliases=DEREF_NEVER,
        )
    except Exception as e:
        log.exception("Failed to search for roles")
        raise e

    roles_found = sorted(
        set({entry.entry_dn.split(",")[1].split("=")[1] for entry in ldap_connection_role_filter.entries})
    )
    log.debug("users found from roles filter: ")
    log.debug(roles_found)

    ldap_connection_role_filter.unbind()

    # generate a list of matches in roles and users
    matched_users = set(users_found) & set(roles_found)
    log.debug("matched users: ")
    log.debug(matched_users)

    # cartesian_product = [(user, role) for user in matched_users for role in roles]

    cartesian_product = list(
        product(
            matched_users,
            roles,
        )
    )
    log.debug("cartesian product: ")
    log.debug(cartesian_product)

    try:
        ldap_connection_action = ldap_connect(
            env.vars.get("LDAP_HOST"),
            env.vars.get("LDAP_USER"),
            env.secrets.get("LDAP_BIND_PASSWORD"),
        )
    except Exception as e:
        log.exception("Failed to connect to LDAP")
        raise e

    for item in cartesian_product:
        if add:
            try:
                ldap_connection_action.add(
                    f"cn={item[1]},cn={item[0]},{user_ou},{root_dn}",
                    attributes={
                        "cn": item[1],
                        "aliasedObjectName": f"cn={item[1]},cn=ndRoleCatalogue,{user_ou},{root_dn}",
                        "objectClass": [
                            "NDRoleAssociation",
                            "alias",
                            "top",
                        ],
                    },
                )
            except Exception as e:
                log.exception(f"Failed to add role '{item[1]}' to user '{item[0]}'")
                raise e
            if ldap_connection_action.result["result"] == 0:
                log.info(f"Successfully added role '{item[1]}' to user '{item[0]}'")
            elif ldap_connection_action.result["result"] == 68:
                log.info(f"Role '{item[1]}' already present for user '{item[0]}'")
            else:
                log.e(f"Failed to add role '{item[1]}' to user '{item[0]}'")
                log.debug(ldap_connection_action.result)
        elif remove:
            ldap_connection_action.delete(f"cn={item[1]},cn={item[0]},{user_ou},{root_dn}")
            if ldap_connection_action.result["result"] == 0:
                log.info(f"Successfully removed role '{item[1]}' from user '{item[0]}'")
            elif ldap_connection_action.result["result"] == 32:
                log.info(f"Role '{item[1]}' already absent for user '{item[0]}'")
            else:
                log.error(f"Failed to remove role '{item[1]}' from user '{item[0]}'")
                log.debug(ldap_connection_action.result)
        else:
            log.error("No action specified")

    if update_notes:
        connection = cli.database.connection()
        log.debug("Created database cursor successfully")
        for user in matched_users:
            try:
                update_sql = """
                UPDATE USER_ SET LAST_UPDATED_DATETIME=CURRENT_DATE,
                LAST_UPDATED_USER_ID=4 WHERE UPPER(DISTINGUISHED_NAME)=UPPER(:user_dn)
                """
                update_cursor = connection.cursor()
                update_cursor.execute(
                    update_sql,
                    [user],
                )
                update_cursor.close()

                insert_sql = """
                            INSERT INTO USER_NOTE (
                                USER_NOTE_ID,
                                USER_ID,
                                LAST_UPDATED_USER_ID,
                                LAST_UPDATED_DATETIME,
                                NOTES
                            )
                            SELECT
                                user_note_id_seq.nextval,
                                USER_ID,
                                4,
                                sysdate,
                                :user_note
                            FROM
                                USER_
                            WHERE
                                UPPER(DISTINGUISHED_NAME) = UPPER(:user_dn)
                        """
                insert_cursor = connection.cursor()
                insert_cursor.setinputsizes(user_note=oracledb.CLOB)
                insert_cursor.execute(
                    insert_sql,
                    user_note=user_note,
                    user_dn=user,
                )
                insert_cursor.close()

                log.info(f"Updated notes for user {user}")
                connection.commit()
                log.info("Committed changes to database successfully")
            except:
                log.exception(f"Failed to update notes for user {user}")
        connection.close()


#########################################
# Deactivate CRC User Accounts
#########################################


def deactivate_crc_users(
    user_ou,
    root_dn,
):
    log.info("Deactivating CRC users")
    ldap_connection = ldap_connect(
        env.vars.get("LDAP_HOST"),
        env.vars.get("LDAP_USER"),
        env.secrets.get("LDAP_BIND_PASSWORD"),
    )

    user_filter = "(userSector=private)(!(userSector=public))(!(endDate=*))(objectclass=NDUser)"

    home_areas = [
        [
            "C01",
            "C02",
            "C03",
            "C04",
            "C05",
            "C06",
            "C07",
            "C08",
            "C09",
            "C10",
            "C11",
            "C12",
            "C13",
            "C14",
            "C15",
            "C16",
            "C17",
            "C18",
            "C19",
            "C20",
            "C21",
        ]
    ]

    found_users = []
    for home_area in home_areas:
        ldap_connection.search(
            ",".join(
                [
                    user_ou,
                    root_dn,
                ]
            ),
            f"(&(userHomeArea={home_area})(!(cn={home_area})){user_filter})",
            attributes=["dn"],
        )

        found_users.append(entry.entry_dn for entry in ldap_connection.entries)

    ldap_connection.search(
        ",".join(
            [
                user_ou,
                root_dn,
            ]
        ),
        f"(&(!(userHomeArea=*)){user_filter})",
        attributes=["dn"],
    )
    found_users_no_home_area = [entry.entry_dn for entry in ldap_connection.entries]

    all_users = found_users + found_users_no_home_area

    date_str = f"{datetime.now().strftime('%Y%m%d')}000000Z"

    for user in all_users:
        ldap_connection.modify(
            user,
            {
                "endDate": [
                    (
                        MODIFY_REPLACE,
                        [date_str],
                    )
                ]
            },
        )

    connection = cli.database.connection()
    for user_dn in all_users:
        try:
            update_sql = (
                f"UPDATE USER_ SET END_DATE=TRUNC(CURRENT_DATE) WHERE UPPER(DISTINGUISHED_NAME)=UPPER(:user_dn)"
            )
            update_cursor = connection.cursor()
            update_cursor.execute(
                update_sql,
                [user_dn],
            )
            update_cursor.close()
            log.info(f"Updated END_DATE for user {user_dn}")
            connection.commit()
            log.info("Committed changes to database successfully")
        except:
            log.exception(f"Failed to update END_DATE for user {user_dn}")
    connection.close()


def user_expiry(
    user_ou,
    root_dn,
):
    date_str = f"{datetime.now().strftime('%Y%m%d')}000000Z"
    log.info(f"Expiring users with end date {date_str}")

    ldap_connection_lock = ldap_connect(
        env.vars.get("LDAP_HOST"),
        env.vars.get("LDAP_USER"),
        env.secrets.get("LDAP_BIND_PASSWORD"),
    )
    try:
        ldap_connection_lock.search(
            ",".join(
                [
                    user_ou,
                    root_dn,
                ]
            ),
            f"(&(!(pwdAccountLockedTime=*))(|(&(endDate=*)(!(endDate>={date_str})))(&(startDate=*)(!(startDate<={date_str})))))",
            attributes=["cn"],
        )
    except Exception as e:
        log.exception(f"Failed to search for users \n Exception: {e}")

    found_users = [entry.entry_dn for entry in ldap_connection_lock.entries]
    log.debug(found_users)
    for user in found_users:
        try:
            ldap_connection_lock.modify(
                user,
                {
                    "pwdAccountLockedTime": [
                        (
                            MODIFY_REPLACE,
                            ["000001010000Z"],
                        )
                    ]
                },
            )
            log.info(f"Locked user {user}")
        except Exception as e:
            log.exception(f"Failed to unlock user {user} \n Exception: {e}")

    ldap_connection_unlock = ldap_connect(
        env.vars.get("LDAP_HOST"),
        env.vars.get("LDAP_USER"),
        env.secrets.get("LDAP_BIND_PASSWORD"),
    )

    try:
        ldap_connection_unlock.search(
            ",".join(
                [
                    user_ou,
                    root_dn,
                ]
            ),
            f"(&(pwdAccountLockedTime=000001010000Z)(|(!(endDate=*))(endDate>={date_str}))(|(!(startDate=*))(startDate<={date_str})))",
            attributes=["cn"],
        )
    except Exception as e:
        log.exception(f"Failed to search for users \n Exception: {e}")

    found_users = [entry.entry_dn for entry in ldap_connection_unlock.entries]
    log.debug(found_users)
    for user in found_users:
        try:
            ldap_connection_unlock.modify(
                user,
                {
                    "pwdAccountLockedTime": [
                        (
                            MODIFY_DELETE,
                            ["000001010000Z"],
                        )
                    ]
                },
            )
            log.info(f"Unlocked user {user}")
        except Exception as e:
            log.exception(f"Failed to unlock user {user} \n Exception: {e}")


def remove_all_user_passwords(
    user_ou,
    root_dn,
):
    log.info("Removing all user passwords")

    ldap_connection = ldap_connect(
        env.vars.get("LDAP_HOST"),
        env.vars.get("LDAP_USER"),
        env.secrets.get("LDAP_BIND_PASSWORD"),
    )

    user_filter = "(!(cn=AutomatedTestUser))"

    try:
        ldap_connection.search(
            ",".join(
                [
                    user_ou,
                    root_dn,
                ]
            ),
            user_filter,
            attributes=["cn"],
            search_scope="LEVEL",
        )
    except Exception as e:
        log.exception("Failed to search for users")
        raise e

    found_users = [entry.entry_dn for entry in ldap_connection.entries]
    log.debug("users found from user filter")
    log.debug(found_users)

    for user in found_users:
        try:
            ldap_connection.modify(
                user,
                {
                    "userPassword": [
                        (
                            MODIFY_DELETE,
                            [],
                        )
                    ]
                },
            )
            log.info(f"Successfully removed passwd for user {user}, or it didn't have one to begin with")
        except Exception as e:
            log.exception(f"Failed to remove passwd for user {user}")
            raise e
    ldap_connection.unbind()
