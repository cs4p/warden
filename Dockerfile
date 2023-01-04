FROM python:3.11-slim-buster as build

WORKDIR /usr/src/

RUN apt update -y && apt install -y apache2-dev apache2

# We copy just the requirements.txt first to leverage Docker cache
COPY ./requirements.txt ./requirements.txt

RUN pip install -r requirements.txt

COPY app ./app
COPY certs/wardencrt.pem ./certs/wardencrt.pem
COPY certs/wardenkey.pem ./certs/wardenkey.pem
COPY certs/warden.crt ./certs/warden.crt
COPY certs/warden.csr ./certs/warden.csr
COPY certs/warden.key ./certs/warden.key
COPY certs/ca.crt ./certs/ca.crt

# Create Service account
RUN useradd -u 1001 flask
RUN chmod -R o+r .

FROM build

USER 1001

#CMD ["mod_wsgi-express", "start-server", "wsgi.py", "--processes", "4"]
CMD ["mod_wsgi-express", "start-server", "app/wsgi.py", "--processes", "4", "--log-to-terminal", "--startup-log", "--https-port", "443", "--https-only", "--server-name", "warden.validation.svc", "--ssl-certificate-file", "certs/warden.crt", "--ssl-certificate-key-file", "certs/warden.key", "--ssl-ca-certificate-file", "certs/ca.crt"]
#ENTRYPOINT [ "python" ]
#
#CMD [ "app/warden.py" ]