
FROM ghcr.io/astral-sh/uv:python3.12-bookworm AS builder
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never

RUN apt-get update && apt-get install -y --no-install-recommends \
    bash \
    ca-certificates \
    git \
    build-essential \
    libffi-dev \
    libldap2-dev \
    ldap-utils \
    python3-dev \
    libssl-dev \
    libsasl2-dev

WORKDIR /code

# Install dependencies
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-project --no-dev

# install cli
COPY . .
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

FROM python:3.12-slim-bookworm
# RUN apk add --update --no-cache bash ca-certificates git build-base libffi-dev openssl-dev gcc musl-dev gcc g++ linux-headers build-base openldap-dev python3-dev
RUN apt-get update && apt-get install -y --no-install-recommends \
    bash \
    ca-certificates \
    git \
    ldap-utils \
    curl \
    unzip \
    libaio1 

# Install Oracle Instant Client
RUN mkdir -p /opt/oracle && \
    curl -L -o /tmp/instantclient.zip https://download.oracle.com/otn_software/linux/instantclient/1927000/instantclient-basic-linux.x64-19.27.0.0.0dbru.zip && \
    unzip /tmp/instantclient.zip -d /opt/oracle && \
    rm /tmp/instantclient.zip
ENV LD_LIBRARY_PATH=/opt/oracle/instantclient_19_27

COPY --from=builder /code /code
ENV PATH="/code/.venv/bin:$PATH"
CMD ["ldap-automation"]

LABEL org.opencontainers.image.source=https://github.com/ministryofjustice/hmpps-ldap-automation-cli