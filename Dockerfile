	
# Use the official Python 3 image.
# https://hub.docker.com/_/python

FROM python:3.8-slim
 
RUN apt-get -y update
RUN apt-get -y install libsasl2-dev python-dev libldap2-dev libssl-dev
RUN apt-get -y install pip

RUN /usr/local/bin/python -m pip install --upgrade pip

COPY ./ldap_sync.py /ldap_sync/
COPY ./libs /ldap_sync/libs
COPY ./plugins /ldap_sync/plugins

COPY ./requirements.txt /ldap_sync/requirements.txt

WORKDIR /ldap_sync

RUN chmod 444 requirements.txt

RUN pip install --no-cache-dir -r requirements.txt

# Run the web service on container startup.
CMD [ "python", "ldap_sync.py", "-c", "/etc/determined/ldap_sync_config.yaml"  ]
