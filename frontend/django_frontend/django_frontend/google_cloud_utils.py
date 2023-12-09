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

from http import HTTPStatus
from os import getenv, environ

from google.auth import default
from google.auth.exceptions import DefaultCredentialsError
from google.auth.transport.requests import Request
from google.cloud import logging
from google.cloud import secretmanager
from requests import get

GCP_CREDENTIALS = None
PROJECT_ID = None


def get_cloud_run_service_name():
    """Only possible within the GCP."""
    return getenv('K_SERVICE', None)


def is_on_google_cloud_platform(env):
    """Only possible within the GCP."""
    # tests do not use the services on GCP
    if env.bool('TEST_MODE', False):
        return False

    if is_on_google_cloud_run():
        return True

    if PROJECT_ID:
        # running on other GCP service
        return True
    else:
        try:
            get_gcp_credentials_and_project_id()
            # running on other GCP service
            return True
        except DefaultCredentialsError:
            return False


def get_gcp_credentials_and_project_id():
    global GCP_CREDENTIALS, PROJECT_ID

    if not PROJECT_ID:
        GCP_CREDENTIALS, PROJECT_ID = default()

    return GCP_CREDENTIALS, PROJECT_ID


def is_on_google_cloud_run():
    """Only possible within the GCP."""
    return 'K_SERVICE' in environ


def get_cloud_run_region_id():
    """Only possible within the GCP."""
    r = get('http://metadata.google.internal/computeMetadata/v1/instance/region',
            headers={'Metadata-Flavor': 'Google'})
    if r.status_code == 200:
        return r.text.split('/')[-1]
    else:
        return EnvironmentError(f'Request for Cloud Run Service region returned HTTP status {r.status_code}: {r.text}')


def get_cloud_run_service_url():
    """Only possible within the GCP."""
    gcp_credentials, project_id = get_login_credentials()

    r = get(f'https://{get_cloud_run_region_id()}-run.googleapis.com/apis/serving.knative.dev/v1/namespaces/'
            f'{project_id}/services/{get_cloud_run_service_name()}',
            headers={'Authorization': f'Bearer {gcp_credentials.token}'})
    if r.status_code == HTTPStatus.OK:
        return r.json()['status']['url']
    else:
        raise EnvironmentError(f'Request for Cloud Run Service URL returned HTTP status {r.status_code}: {r.text}')


def get_login_credentials():
    """Only possible within the GCP."""
    gcp_credentials, project_id = get_gcp_credentials_and_project_id()

    auth_req = Request()
    gcp_credentials.refresh(auth_req)

    return gcp_credentials, project_id


class SecretManager(object):
    def __init__(self, project_id):
        self._client = secretmanager.SecretManagerServiceClient()
        self._project_id = project_id

    def load(self, secret_id, version_id):
        secret_name = f'projects/{self._project_id}/secrets/{secret_id}/versions/{version_id}'
        response = self._client.access_secret_version(request={'name': secret_name})

        return response.payload.data.decode('UTF-8')


def load_db_password_from_secret_manager():
    _, gcp_project_id = get_gcp_credentials_and_project_id()
    secrets = SecretManager(gcp_project_id)

    db_frontend_user_password = secrets.load(
        environ.get('DB_FRONTEND_DB_PASSWORD_SECRET'),
        environ.get('DB_FRONTEND_DB_PASSWORD_SECRET_VERSION')
    )

    return db_frontend_user_password


def load_environment_from_secret_manager():
    _, gcp_project_id = get_gcp_credentials_and_project_id()
    secrets = SecretManager(gcp_project_id)
    return secrets.load(environ.get('SECRET_DJANGO_SECRET_KEY_NAME'), 'latest')


def configure_gcp_logging():
    client = logging.Client()
    client.setup_logging()

    return client
