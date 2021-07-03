#  Remote Weather Access - Client/server solution for distributed weather networks
#   Copyright (C) 2013-2021 Ralf Rettig (info@personalfme.de)
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU Affero General Public License as
#   published by the Free Software Foundation, either version 3 of the
#   License, or (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU Affero General Public License for more details.
#
#   You should have received a copy of the GNU Affero General Public License
#   along with this program.  If not, see <https://www.gnu.org/licenses/>.

import os
from datetime import timedelta
from multiprocessing import Process, Pipe
from urllib.parse import quote_plus


class Config(object):
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY')
    DB_PORT = os.environ.get('DB_PORT', 5432)
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    BCRYPT_LOG_ROUNDS = 13
    TIMEZONE = os.environ.get('TIMEZONE', 'Europe/Berlin')
    SQLALCHEMY_ENGINE_OPTIONS = {
        'connect_args': {
            'options': '-c timezone={}'.format(TIMEZONE)
        },
        'pool_pre_ping': True
    }


class ProdConfig(Config):
    ENV = 'prod'
    DEBUG = False
    DB_URL = os.environ.get('DB_URL', '')
    # configured for Google Cloud SQL
    DB_INSTANCE_CONNECTION_NAME = '/cloudsql/' + os.environ.get('DB_INSTANCE_CONNECTION_NAME', '')
    DB_USER_DB_USER = os.environ.get('DB_USER_DB_USER')
    DB_USER_DB_PASSWORD = os.environ.get('DB_USER_DB_PASSWORD')
    DB_USER_DATABASE = os.environ.get('DB_USER_DATABASE')
    DB_WEATHER_DB_USER = os.environ.get('DB_WEATHER_DB_USER')
    DB_WEATHER_DB_PASSWORD = os.environ.get('DB_WEATHER_DB_PASSWORD')
    DB_WEATHER_DATABASE = os.environ.get('DB_WEATHER_DATABASE')
    SQLALCHEMY_DATABASE_URI = None
    SQLALCHEMY_BINDS = {
        'weather-data': ''
    }
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=1)

    def __init__(self):
        if 'RUNNING_ON_SERVER' in os.environ:
            # assumes a Unix socket connection
            gcp_project_id = ProdConfig._get_gcp_project_id_in_subprocess()
            if gcp_project_id:
                secrets = ProdConfig._load_from_google_secret_manager_in_subprocess(gcp_project_id)
                ProdConfig.DB_USER_DB_PASSWORD, ProdConfig.DB_WEATHER_DB_PASSWORD, ProdConfig.JWT_SECRET_KEY = secrets

            user_db_password, weather_db_password = self._quote_sql_passwords()

            ProdConfig.SQLALCHEMY_DATABASE_URI = 'postgresql+psycopg2://{}:{}@/{}?host={}'.format(
                ProdConfig.DB_USER_DB_USER,
                user_db_password,
                ProdConfig.DB_USER_DATABASE,
                ProdConfig.DB_INSTANCE_CONNECTION_NAME
            )

            ProdConfig.SQLALCHEMY_BINDS['weather-data'] = 'postgresql+psycopg2://{}:{}@/{}?host={}'.format(
                ProdConfig.DB_WEATHER_DB_USER,
                weather_db_password,
                ProdConfig.DB_WEATHER_DATABASE,
                ProdConfig.DB_INSTANCE_CONNECTION_NAME
            )
        else:
            user_db_password, weather_db_password = self._quote_sql_passwords()

            ProdConfig.SQLALCHEMY_DATABASE_URI = 'postgresql+psycopg2://{}:{}@{}:{}/{}'.format(
                ProdConfig.DB_USER_DB_USER,
                user_db_password,
                ProdConfig.DB_URL, Config.DB_PORT,
                ProdConfig.DB_USER_DATABASE
            )

            ProdConfig.SQLALCHEMY_BINDS['weather-data'] = 'postgresql+psycopg2://{}:{}@{}:{}/{}'.format(
                ProdConfig.DB_WEATHER_DB_USER,
                weather_db_password,
                ProdConfig.DB_URL, Config.DB_PORT,
                ProdConfig.DB_WEATHER_DATABASE
            )

    @staticmethod
    def _quote_sql_passwords():
        if ProdConfig.DB_USER_DB_PASSWORD:
            user_db_password = quote_plus(ProdConfig.DB_USER_DB_PASSWORD)
        else:
            user_db_password = None

        if ProdConfig.DB_WEATHER_DB_PASSWORD:
            weather_db_password = quote_plus(ProdConfig.DB_WEATHER_DB_PASSWORD)
        else:
            weather_db_password = None

        return user_db_password, weather_db_password

    @staticmethod
    def _get_gcp_project_id_in_subprocess():
        # run in a subprocess to prevent issues with gevent-unpatched SSL-connections later
        parent_conn, child_conn = Pipe()
        p = Process(target=ProdConfig._get_gcp_project_id, args=(child_conn,))
        p.start()
        gcp_project_id = parent_conn.recv()
        p.join()
        return gcp_project_id

    @staticmethod
    def _get_gcp_project_id(conn):
        from backend_src.google_cloud_utils import get_project_id
        gcp_project_id = get_project_id()
        conn.send(gcp_project_id)
        conn.close()

    @staticmethod
    def _load_from_google_secret_manager_in_subprocess(gcp_project_id):
        # run in a subprocess to prevent issues with gevent-unpatched SSL-connections later
        parent_conn, child_conn = Pipe()
        p = Process(target=ProdConfig._load_from_google_secret_manager, args=(child_conn, gcp_project_id))
        p.start()
        secrets = parent_conn.recv()
        if isinstance(secrets, str):
            raise AssertionError(secrets)
        p.join()
        return secrets

    @staticmethod
    def _load_from_google_secret_manager(conn, gcp_project_id):
        try:
            from backend_src.google_cloud_utils import SecretManager
            secrets = SecretManager(gcp_project_id)

            db_user_db_password = secrets.load(
                os.environ.get('DB_USER_DB_PASSWORD_SECRET'),
                os.environ.get('DB_USER_DB_PASSWORD_SECRET_VERSION')
            )

            db_weather_db_password = secrets.load(
                os.environ.get('DB_WEATHER_DB_PASSWORD_SECRET'),
                os.environ.get('DB_WEATHER_DB_PASSWORD_SECRET_VERSION')
            )

            jwt_secret_key = secrets.load(
                os.environ.get('JWT_SECRET_KEY_SECRET'),
                os.environ.get('JWT_SECRET_KEY_SECRET_VERSION')
            )

            conn.send((db_user_db_password, db_weather_db_password, jwt_secret_key))
        except Exception as e:
            conn.send('ERROR loading secrets: {}'.format(e))
        finally:
            conn.close()


class DevConfig(Config):
    ENV = 'dev'
    DEBUG = True
    DB_URL = 'localhost'
    DB_USER = 'postgres'
    DB_PASSWORD = os.environ.get('DB_PASSWORD', 'passwd')
    DB_DATABASE = 'postgres'
    SQLALCHEMY_DATABASE_URI = 'postgresql+psycopg2://{}:{}@{}:{}/{}'.format(DB_USER, quote_plus(DB_PASSWORD), DB_URL,
                                                                            Config.DB_PORT, DB_DATABASE)
    SQLALCHEMY_BINDS = {
        'weather-data': 'postgresql+psycopg2://{}:{}@{}:{}/{}'.format(DB_USER, quote_plus(DB_PASSWORD), DB_URL,
                                                                      Config.DB_PORT, DB_DATABASE)
    }
    JWT_SECRET_KEY = 'SECRET-KEY'
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)


class TestConfig(Config):
    ENV = 'test'
    TESTING = True
    DEBUG = True
    DB_URL = os.environ.get('POSTGRES_TEST_URL', 'localhost')
    DB_USER = 'postgres'
    DB_PASSWORD = os.environ.get('DB_PASSWORD', 'passwd')
    DB_DATABASE = 'postgres'
    SQLALCHEMY_DATABASE_URI = 'postgresql+psycopg2://{}:{}@{}:{}/{}'.format(DB_USER, quote_plus(DB_PASSWORD), DB_URL,
                                                                            Config.DB_PORT, DB_DATABASE)
    SQLALCHEMY_BINDS = {
        'weather-data': 'postgresql+psycopg2://{}:{}@{}:{}/{}'.format(DB_USER, quote_plus(DB_PASSWORD), DB_URL,
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
