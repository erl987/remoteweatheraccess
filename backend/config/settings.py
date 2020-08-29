import os
from datetime import timedelta


class Config(object):
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY')
    DB_PORT = os.environ.get('DB_PORT', 5432)
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    BCRYPT_LOG_ROUNDS = 13
    TIMEZONE = 'Europe/Berlin'
    SQLALCHEMY_ENGINE_OPTIONS = {
        'connect_args': {
            'options': '-c timezone={}'.format(TIMEZONE)
        }
    }


class ProdConfig(Config):
    ENV = 'prod'
    DEBUG = False
    DB_URL = os.environ.get('DB_URL')
    DB_USER_DB_USER = os.environ.get('DB_USER_DB_USER')
    DB_USER_DB_PASSWORD = os.environ.get('DB_USER_DB_PASSWORD')
    DB_USER_DATABASE = os.environ.get('DB_USER_DATABASE')
    DB_WEATHER_DB_USER = os.environ.get('DB_WEATHER_DB_USER')
    DB_WEATHER_DB_PASSWORD = os.environ.get('DB_WEATHER_DB_PASSWORD')
    DB_WEATHER_DATABASE = os.environ.get('DB_WEATHER_DATABASE')
    SQLALCHEMY_DATABASE_URI = 'postgresql+psycopg2://{}:{}@{}:{}/{}'.format(DB_USER_DB_USER, DB_USER_DB_PASSWORD,
                                                                            DB_URL, Config.DB_PORT, DB_USER_DATABASE)
    SQLALCHEMY_BINDS = {
        'weather-data': 'postgresql+psycopg2://{}:{}@{}:{}/{}'.format(DB_WEATHER_DB_USER, DB_WEATHER_DB_PASSWORD,
                                                                      DB_URL, Config.DB_PORT, DB_WEATHER_DATABASE)
    }
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=1)


class DevConfig(Config):
    ENV = 'dev'
    DEBUG = True
    DB_URL = 'localhost'
    DB_USER = 'postgres'
    DB_PASSWORD = os.environ.get('DB_PASSWORD', 'passwd')
    DB_DATABASE = 'postgres'
    SQLALCHEMY_DATABASE_URI = 'postgresql+psycopg2://{}:{}@{}:{}/{}'.format(DB_USER, DB_PASSWORD, DB_URL,
                                                                            Config.DB_PORT, DB_DATABASE)
    SQLALCHEMY_BINDS = {
        'weather-data': 'postgresql+psycopg2://{}:{}@{}:{}/{}'.format(DB_USER, DB_PASSWORD, DB_URL,
                                                                      Config.DB_PORT, DB_DATABASE)
    }
    JWT_SECRET_KEY = 'SECRET-KEY'
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)


class TestConfig(Config):
    ENV = 'test'
    TESTING = True
    DEBUG = True
    DB_URL = 'localhost'
    DB_USER = 'postgres'
    DB_PASSWORD = os.environ.get('DB_PASSWORD', 'passwd')
    DB_DATABASE = 'postgres'
    SQLALCHEMY_DATABASE_URI = 'postgresql+psycopg2://{}:{}@{}:{}/{}'.format(DB_USER, DB_PASSWORD, DB_URL,
                                                                            Config.DB_PORT, DB_DATABASE)
    SQLALCHEMY_BINDS = {
        'weather-data': 'postgresql+psycopg2://{}:{}@{}:{}/{}'.format(DB_USER, DB_PASSWORD, DB_URL,
                                                                      Config.DB_PORT, DB_DATABASE)
    }
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
