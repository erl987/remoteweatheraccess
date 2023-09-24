#  Remote Weather Access - Client/server solution for distributed weather networks
#   Copyright (C) 2013-2023 Ralf Rettig (info@personalfme.de)
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

"""
Django settings for django_frontend project.

Generated by 'django-admin startproject' using Django 3.2.5.

For more information on this file, see
https://docs.djangoproject.com/en/3.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.2/ref/settings/
"""
from datetime import timedelta
from locale import setlocale, LC_ALL
from multiprocessing import Process
from os import getenv, path, environ
from pathlib import Path
from urllib.parse import urlparse

from environ import Env

from .google_cloud_utils import get_cloud_run_service_url, load_db_password_from_secret_manager, \
    load_environment_from_secret_manager, get_cloud_run_service_name, is_on_google_cloud_platform, \
    is_on_google_cloud_run, configure_gcp_logging
from .utils import trigger_startup_of_backend_service

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent
SITE_ROOT = BASE_DIR

# Django-environ setup
env = Env()

IS_ON_GOOGLE_CLOUD_PLATFORM = is_on_google_cloud_platform(env)

env_file = getenv('ENV_PATH', None)
if env_file and path.isfile(env_file):
    env.read_env(env_file)
    print(f'Using environment file: {env_file}')

elif IS_ON_GOOGLE_CLOUD_PLATFORM:
    load_environment_from_secret_manager(env)
    print(f'Using environment from Google Secret Manager')

else:
    raise FileNotFoundError('No local .env file and not running on Google Cloud Run')

# trigger the startup of the backend service as early as possible
p = Process(target=trigger_startup_of_backend_service)
p.start()

SECRET_KEY = env.str('SECRET_KEY')

if IS_ON_GOOGLE_CLOUD_PLATFORM:
    DEBUG = False
else:
    DEBUG = env.bool('DEBUG', default=False)
TEMPLATE_DEBUG = DEBUG

if IS_ON_GOOGLE_CLOUD_PLATFORM:
    database_password = load_db_password_from_secret_manager()
else:
    database_password = None

if is_on_google_cloud_run():
    cloud_run_service_url = get_cloud_run_service_url()

    ALLOWED_HOSTS = ([urlparse(cloud_run_service_url).netloc] +
                     [urlparse(url).netloc for url in env.list('ALLOWED_URLS')])
    CSRF_TRUSTED_ORIGINS = [cloud_run_service_url] + env.list('ALLOWED_URLS')
    SECURE_SSL_REDIRECT = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SECURE_HSTS_PRELOAD = True
    SECURE_HSTS_SECONDS = 3600
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_BROWSER_XSS_FILTER = True
    CSRF_COOKIE_SECURE = True
    SESSION_COOKIE_SECURE = True
    X_FRAME_OPTIONS = "DENY"
else:
    ALLOWED_HOSTS = ['*']

# Application definition

INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'weatherpage.apps.WeatherpageConfig',
    'django_plotly_dash.apps.DjangoPlotlyDashConfig',
    'crispy_forms',
    'crispy_bootstrap4'
]

CRISPY_TEMPLATE_PACK = 'bootstrap4'

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django_plotly_dash.middleware.BaseMiddleware'
]

ROOT_URLCONF = 'django_frontend.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'django_frontend.wsgi.application'

# Database
# https://docs.djangoproject.com/en/3.2/ref/settings/#databases

if IS_ON_GOOGLE_CLOUD_PLATFORM:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': env.str('DB_FRONTEND_DATABASE'),
            'USER': env.str('DB_FRONTEND_DB_USER'),
            'PASSWORD': database_password,
            # configured for Google Cloud SQL
            'HOST': '/cloudsql/' + env.str('DB_INSTANCE_CONNECTION_NAME')
        }
    }
else:
    DATABASES = {
        'default': env.db()
    }

# Password validation
# https://docs.djangoproject.com/en/3.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
# https://docs.djangoproject.com/en/3.2/topics/i18n/

LANGUAGE_CODE = env.str('LANGUAGE_CODE').split('_')[0]

# server time zone
TIME_ZONE = env.str('TIME_ZONE')

USE_I18N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.2/howto/static-files/

if env.str('FILE_STORAGE') == 'S3':
    STORAGES = {
        'default': {
            'BACKEND': 'storages.backends.s3boto3.S3StaticStorage'
        },
        'staticfiles': {
            'BACKEND': 'storages.backends.s3boto3.S3StaticStorage'
        }
    }

    AWS_S3_ENDPOINT_URL = env.str('S3_ENDPOINT_URL')
    AWS_ACCESS_KEY_ID = env.str('S3_ACCESS_KEY')
    AWS_SECRET_ACCESS_KEY = env.str('S3_SECRET_ACCESS_KEY')
    AWS_STORAGE_BUCKET_NAME = env.str('S3_STORAGE_BUCKET_NAME')
    AWS_S3_USE_SSL = False
    STATIC_URL = f'{env.str("S3_ENDPOINT_URL")}/{AWS_STORAGE_BUCKET_NAME}/'
elif env.str('FILE_STORAGE') == 'GCS':
    STORAGES = {
        'default': {
            'BACKEND': 'storages.backends.gcloud.GoogleCloudStorage'
        },
        'staticfiles': {
            'BACKEND': 'storages.backends.gcloud.GoogleCloudStorage'
        }
    }

    GS_BUCKET_ADDRESS = env.str('FRONTEND_BUCKET')
    GS_BUCKET_NAME = GS_BUCKET_ADDRESS.replace('gs://', '')
    GS_BUCKET_NAME = GS_BUCKET_NAME.replace('/', '')
    STATIC_URL = f'https://storage.googleapis.com/{GS_BUCKET_NAME}/'

    if is_on_google_cloud_run():
        GS_DEFAULT_ACL = 'publicRead'
else:
    raise AssertionError(f'Unknown file storage option {env.str("FILE_STORAGE")}')

# Default primary key field type
# https://docs.djangoproject.com/en/3.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'
    }
}

# Logging

if is_on_google_cloud_run():
    client = configure_gcp_logging()

    LOGGING = {
        'version': 1,
        'disable_existing_loggers': False,
        'handlers': {
            'stackdriver': {
                'class': 'google.cloud.logging.handlers.CloudLoggingHandler',
                'client': client
            }
        },
        'loggers': {
            'django': {
                'handlers': ['stackdriver'],
                'level': 'INFO'
            }
        },
    }

if 'TEST_MODE' not in environ:
    setlocale(LC_ALL, env.str('LANGUAGE_CODE'))
