import os
from datetime import timedelta


class Config(object):
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    PROJECT_ROOT = os.environ.get('BASEDIR', os.path.abspath(os.path.dirname(os.path.dirname(__file__))))
    DB_PATH = os.path.join(PROJECT_ROOT, 'instance')
    BCRYPT_LOG_ROUNDS = 13


class ProdConfig(Config):
    ENV = 'prod'
    DEBUG = False
    DB_NAME = 'weather-backend.sqlite'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///' + os.path.join(Config.DB_PATH, DB_NAME))
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=1)


class DevConfig(Config):
    ENV = 'dev'
    DEBUG = True
    DB_NAME = 'weather-backend-dev.sqlite'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(Config.DB_PATH, DB_NAME) + "?check_same_thread=False"
    JWT_SECRET_KEY = 'SECRET-KEY'
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)


class TestConfig(Config):
    ENV = 'test'
    TESTING = True
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'sqlite://'
    JWT_SECRET_KEY = 'SECRET-KEY'
    BCRYPT_LOG_ROUNDS = 4  # for faster tests; needs at least 4 to avoid "ValueError: Invalid rounds"
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
