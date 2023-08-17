import logging

from cli import config
from cli.ldap import ldap_connect


##
# Original ansible to replicate then remove
##
        # - name: Search for matching users (Home Area=Old value, Active)
        #   shell: >
        #     ldapsearch -LLL -H ldap:// -D cn=root,dc=moj,dc=com -w "${ldap_admin_password}" -b {{ user_dn }} -s one \
        #     '(&(objectclass=NDUser)(userHomeArea={{ old_home_area }})(!(cn={{ old_home_area }}))(!(endDate=*)))' dn \
        #     | sed 's/^$/changetype: modify\nreplace: userHomeArea\nuserHomeArea: {{ new_home_area }}\n/' \
        #     > {{ workspace }}/update.ldif
        #   environment:
        #     ldap_admin_password: '{{ ldap_admin_password.stdout }}'

        # - name: Create additional LDIF for deleting home areas (required due to LDAP issue causing old values to get "stuck")
        #   shell: >
        #     cat {{ workspace }}/update.ldif \
        #     | sed 's/replace: userHomeArea/delete: userHomeArea/' \
        #     | sed 's/userHomeArea: {{ new_home_area }}/userHomeArea: {{ old_home_area }}/' \
        #     > {{ workspace }}/delete.ldif

        # - name: Apply changes
        #   shell: ldapmodify -Y EXTERNAL -H ldapi:// -c -f {{ workspace }}/update.ldif 2>&1 | tee {{ workspace }}/update.log

        # - name: Restart LDAP (required due to LDAP issue causing old values to get "stuck")
        #   shell: systemctl restart slapd

        # - name: Force deletion of old home area (required due to LDAP issue causing old values to get "stuck")
        #   shell: ldapmodify -Y EXTERNAL -H ldapi:// -c -f {{ workspace }}/delete.ldif 2>&1 | tee {{ workspace }}/delete.log


def update_user_home_areas(old_home_area, new_home_area):
        logging.info(f"Updating user home areas from {old_home_area} to {new_home_area}")
        ldap_connection = ldap_connect(config.ldap_host, config.ldap_user, config.ldap_password)
        ldap_connection.search("ou=Users,dc=moj,dc=com", f"(&(objectclass=NDUser)(userHomeArea={old_home_area})(!(cn={old_home_area}))(!(endDate=*)))")
        records = ldap_connection.response
        logging.info(len(records))
        for record in records:  
                logging.info(record)
