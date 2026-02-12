# syntax = docker/dockerfile:1.3
# Use the official Python 3 image.
# https://hub.docker.com/_/python
#FROM python:3.8.16-slim
FROM python:3.15.0a6-slim

ARG DEBIAN_FRONTEND=noninteractive
RUN apt-get -y update \
 && apt-get -y install \
      libsasl2-dev \
      build-essential \
      python3-dev \
      python-dev-is-python3 \
      libldap2-dev \
      libssl-dev \
 && apt-get -y clean

# Virtual environment creation
ENV VIRTUAL_ENV=/opt/venv
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
# ---

COPY ldap_sync/ /ldap_sync/
WORKDIR /ldap_sync

ARG CONFIGDIR=/etc/determined
RUN mkdir -p $CONFIGDIR \
 && chmod 0755 $CONFIGDIR \
 && chmod 0444 requirements.txt 

RUN pip install --no-cache-dir -r requirements.txt

# Run the web service on container startup.
CMD [ "python", "ldap_sync.py", "-c", "/etc/determined/ldap_sync_config.yaml"  ]
