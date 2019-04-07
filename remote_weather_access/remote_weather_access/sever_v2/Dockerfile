FROM python:3.7.2-alpine3.9

RUN pip install gunicorn json-logging-py flask-marshmallow flask-sqlalchemy marshmallow-sqlalchemy pytz

COPY config/* /

COPY server.py wsgi.py /

EXPOSE 8000

ENTRYPOINT ["/usr/local/bin/gunicorn", "--config", "/gunicorn.conf", "--log-config", "/logging.conf", "-b", ":8000", "server:app"]
