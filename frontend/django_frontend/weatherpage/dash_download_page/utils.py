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

from os import getenv, environ

from google.cloud.storage import Client

from frontend.django_frontend.django_frontend.google_cloud_utils import is_on_google_cloud_run
from ..dash_weatherpage.backend_proxy import CachedBackendProxy
from ..dash_weatherpage.dash_settings import BACKEND_URL, BACKEND_PORT, BACKEND_DO_USE_HTTPS


def get_storage_client():
    service_account_json = getenv('GCP_SERVICE_ACCOUNT_JSON', None)
    if service_account_json:
        storage_client = Client.from_service_account_json(service_account_json)
    else:
        storage_client = Client()

    return storage_client


def is_deployed_environment():
    return is_on_google_cloud_run() or 'DOCKER_COMPOSE_APP' in environ


def get_bucket_id():
    bucket_address = environ['EXPORTER_BUCKET_NAME']
    bucket_id = bucket_address.replace('gs://', '')
    bucket_id = bucket_id.replace('/', '')

    return bucket_id


def get_station_id(requested_station_label, station_label_info_from_backend):
    requested_station_id = None
    for station_id, station_label in station_label_info_from_backend.items():
        if station_label == requested_station_label:
            requested_station_id = station_id
            break

    if not requested_station_id:
        raise AssertionError(f'No station metadata in the backend database for the provided station label '
                             f'{requested_station_label}')

    return requested_station_id


def get_station_label_info_from_backend():
    available_stations, _, _ = CachedBackendProxy(BACKEND_URL, BACKEND_PORT, BACKEND_DO_USE_HTTPS).available_stations()
    return {station['value']: station['label'] for station in available_stations}
