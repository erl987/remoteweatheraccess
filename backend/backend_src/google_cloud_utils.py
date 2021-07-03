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
import requests


class SecretManager(object):
    def __init__(self, project_id):
        from google.cloud import secretmanager

        self._client = secretmanager.SecretManagerServiceClient()
        self._project_id = project_id

    def load(self, secret_id, version_id):
        secret_name = 'projects/{}/secrets/{}/versions/{}'.format(self._project_id, secret_id, version_id)
        response = self._client.access_secret_version(name=secret_name)

        return response.payload.data.decode('UTF-8')


def get_project_id():
    """Obtains the instance metadata (which is only possible if this is running in the GCP)"""
    # noinspection PyBroadException
    try:
        r = requests.get('http://metadata.google.internal/computeMetadata/v1/project/project-id',
                         headers={'Metadata-Flavor': 'Google'})
        if r.status_code == 200:
            return r.text
        else:
            return None
    except Exception:
        return None
