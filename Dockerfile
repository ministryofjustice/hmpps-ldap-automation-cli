FROM python:3.10-alpine

LABEL org.opencontainers.image.source = "https://github.com/ministryofjustice/hmpps-ldap-automation-cli"

ARG VERSION_REF=main

# Basic tools for now
RUN apk add --update --no-cache bash ca-certificates git build-base libffi-dev openssl-dev gcc musl-dev gcc g++ linux-headers build-base openldap-dev python3-dev

RUN python3 -m pip install --upgrade pip && python3 -m pip install git+https://github.com/ministryofjustice/hmpps-ldap-automation-cli.git@${VERSION_REF}

CMD ["ldap-automation"]
