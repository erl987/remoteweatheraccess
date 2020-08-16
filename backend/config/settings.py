import os
from datetime import timedelta


class Config(object):
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    BCRYPT_LOG_ROUNDS = 13


class ProdConfig(Config):
    ENV = 'prod'
    DEBUG = False
    DB_URL = os.environ.get('DB_URL')
    DB_PORT = os.environ.get('DB_PORT', 5432)
    DB_USER = os.environ.get('DB_USER')
    DB_PASSWORD = os.environ.get('DB_PASSWORD')
    DB_DATABASE = os.environ.get('DB_DATABASE')
    SQLALCHEMY_DATABASE_URI = 'postgresql+psycopg2://{}:{}@{}:{}/{}'.format(DB_USER, DB_PASSWORD, DB_URL, DB_PORT,
                                                                            DB_DATABASE)
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=1)


class DevConfig(Config):
    ENV = 'dev'
    DEBUG = True
    DB_URL = 'localhost'
    DB_PORT = 5432
    DB_USER = 'postgres'
    DB_PASSWORD = os.environ.get('DB_PASSWORD', 'passwd')
    DB_DATABASE = 'postgres'
    SQLALCHEMY_DATABASE_URI = 'postgresql+psycopg2://{}:{}@{}:{}/{}'.format(DB_USER, DB_PASSWORD, DB_URL, DB_PORT,
                                                                            DB_DATABASE)
    JWT_SECRET_KEY = 'SECRET-KEY'
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)


class TestConfig(Config):
    ENV = 'test'
    TESTING = True
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'sqlite://'
    JWT_SECRET_KEY = 'SECRET-KEY'
    BCRYPT_LOG_ROUNDS = 4  # for faster tests; needs at least 4 to avoid 'ValueError: Invalid rounds'
    JWT_HEADER_TYPE = 'Bearer'
    JWT_BLACKLIST_ENABLED = False
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=1)


LOGGING_CONFIG = {
    'version': 1,
    'formatters': {'default': {
        'format': '[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
    }},
    'handlers': {'wsgi': {
        'class': 'logging.StreamHandler',
        'stream': 'ext://flask.logging.wsgi_errors_stream',
        'formatter': 'default'
    }},
    'root': {
        'level': 'INFO',
        'handlers': ['wsgi']
    }
}
