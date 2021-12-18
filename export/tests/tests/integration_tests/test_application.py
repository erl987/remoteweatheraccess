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
import pathlib
from unittest.mock import patch

import requests_mock
from fastapi.testclient import TestClient
from google.api_core import exceptions

from ..utils import set_mocks_up, csv_files_do_match

URL = 'something'
PORT = 443

SENSOR_RESPONSE = [
    {'description': 'UV', 'sensor_id': 'uv', 'unit': 'UV-X'},
    {'description': 'Temperatur', 'sensor_id': 'temperature', 'unit': '°C'}]

STATION_RESPONSE = [
    {'device': 'TE923', 'height': 520.0, 'id': 5, 'latitude': -20.23425, 'location': 'Test place/TE/LA',
     'longitude': 40.0234, 'rain_calib_factor': 0.6820802083333333, 'station_id': 'TES'}]

DATA_RESPONSE = {
    'TES': {
        'timepoint': ['2021-12-01T00:00:00+01:00', '2021-12-01T00:10:00+01:00', '2021-12-01T00:20:00+01:00',
                      '2021-12-01T00:30:00+01:00', '2021-12-01T00:40:00+01:00', '2021-12-01T00:50:00+01:00',
                      '2021-12-01T01:00:00+01:00', '2021-12-01T01:10:00+01:00', '2021-12-01T01:20:00+01:00',
                      '2021-12-01T01:30:00+01:00', '2021-12-01T01:40:00+01:00', '2021-12-01T01:50:00+01:00'],
        'uv': [8.7, 9.3, 8.3, 6.5, 4.3, 6.5, 7.4, 10.5, 8.9, 7.7, 6.5, 6.2],
        'temperature_humidity': {
            'OUT1': {
                'temperature': [3.4, 3.4, 3.5, 3.5, 3.5, 3.5, 3.4, -0.5, -2.5, -2.1, 3.5, 3.5]
            }
        }
    }
}

EXPECTED_FILE_NAME = 'EXP12_21.csv'
REFERENCE_DATA_PATH = r'./reference_data'

base_path = pathlib.Path(__file__).parent.resolve()


@patch.dict(os.environ, {'BACKEND_URL': URL})
@patch.dict(os.environ, {'BACKEND_PORT': str(PORT)})
@patch.dict(os.environ, {'BUCKET_ID': 'a-bucket-id-###'})
@patch('export_src.utils.get_bucket_id')
@patch('google.cloud.storage.Client')
def test_regular_run(storage_client, get_bucket_id, tmpdir):
    csv_file_destination_dir = os.path.abspath(tmpdir.mkdir('csv_files'))
    expected_csv_file_path = os.path.join(csv_file_destination_dir, EXPECTED_FILE_NAME)
    reference_csv_file_path = os.path.join(base_path, REFERENCE_DATA_PATH, r'./regular', EXPECTED_FILE_NAME)

    with patch.dict(os.environ, {'CSV_FILE_DIR': csv_file_destination_dir}):
        from export_app import app

        with patch('os.path.getsize') as os_get_size:
            bucket_mock, object_blob_mock = set_mocks_up(get_bucket_id, os_get_size, storage_client)

            client = TestClient(app)

            with requests_mock.Mocker(real_http=True) as m:
                m.get('https://{}:{}/api/v1/sensor'.format(URL, PORT), json=SENSOR_RESPONSE)
                m.get('https://{}:{}/api/v1/station'.format(URL, PORT), json=STATION_RESPONSE)
                m.get('https://{}:{}/api/v1/data'.format(URL, PORT), json=DATA_RESPONSE)
                response = client.post('/upload')
                assert response.status_code == 200

                assert bucket_mock.blob.call_count == 1
                assert bucket_mock.blob.call_args[0][0] == os.path.join('TES', EXPECTED_FILE_NAME)
                assert object_blob_mock.upload_from_filename.call_count == 1
                assert object_blob_mock.upload_from_filename.call_args[1]['filename'] == expected_csv_file_path

                assert csv_files_do_match(expected_csv_file_path, reference_csv_file_path)


@patch.dict(os.environ, {'BACKEND_URL': URL})
@patch.dict(os.environ, {'BACKEND_PORT': str(PORT)})
def test_when_backend_api_fails(tmpdir):
    csv_file_destination_dir = os.path.abspath(tmpdir.mkdir('csv_files'))

    with patch.dict(os.environ, {'CSV_FILE_DIR': csv_file_destination_dir}):
        from export_app import app

        client = TestClient(app)

        with requests_mock.Mocker(real_http=True) as m:
            m.get('https://{}:{}/api/v1/sensor'.format(URL, PORT), json=SENSOR_RESPONSE, status_code=500)
            response = client.post('/upload')
            assert response.status_code == 503


@patch.dict(os.environ, {'BACKEND_URL': URL})
@patch.dict(os.environ, {'BACKEND_PORT': str(PORT)})
def test_when_month_is_no_int(tmpdir):
    csv_file_destination_dir = os.path.abspath(tmpdir.mkdir('csv_files'))

    with patch.dict(os.environ, {'CSV_FILE_DIR': csv_file_destination_dir}):
        from export_app import app

        client = TestClient(app)

        response = client.post('/upload?month=abc&year=2021')
        assert response.status_code == 422


@patch.dict(os.environ, {'BACKEND_URL': URL})
@patch.dict(os.environ, {'BACKEND_PORT': str(PORT)})
def test_when_month_is_out_of_range(tmpdir):
    csv_file_destination_dir = os.path.abspath(tmpdir.mkdir('csv_files'))

    with patch.dict(os.environ, {'CSV_FILE_DIR': csv_file_destination_dir}):
        from export_app import app

        client = TestClient(app)

        with requests_mock.Mocker(real_http=True) as m:
            m.get('https://{}:{}/api/v1/sensor'.format(URL, PORT), json=SENSOR_RESPONSE, status_code=500)
            response = client.post('/upload?month=13&year=2021')
            assert response.status_code == 422


@patch.dict(os.environ, {'BACKEND_URL': URL})
@patch.dict(os.environ, {'BACKEND_PORT': str(PORT)})
def test_when_month_is_out_of_range(tmpdir):
    csv_file_destination_dir = os.path.abspath(tmpdir.mkdir('csv_files'))

    with patch.dict(os.environ, {'CSV_FILE_DIR': csv_file_destination_dir}):
        from export_app import app

        client = TestClient(app)

        response = client.post('/upload?month=13&year=2021')
        assert response.status_code == 422


@patch.dict(os.environ, {'BACKEND_URL': URL})
@patch.dict(os.environ, {'BACKEND_PORT': str(PORT)})
def test_when_station_id_is_invalid(tmpdir):
    csv_file_destination_dir = os.path.abspath(tmpdir.mkdir('csv_files'))

    with patch.dict(os.environ, {'CSV_FILE_DIR': csv_file_destination_dir}):
        from export_app import app

        client = TestClient(app)

        with requests_mock.Mocker(real_http=True) as m:
            m.get('https://{}:{}/api/v1/sensor'.format(URL, PORT), json=SENSOR_RESPONSE)
            m.get('https://{}:{}/api/v1/station'.format(URL, PORT), json=STATION_RESPONSE)
            m.get('https://{}:{}/api/v1/data'.format(URL, PORT), json=DATA_RESPONSE)
            response = client.post('/upload?station_id=ANY')
            assert response.status_code == 422


@patch.dict(os.environ, {'BACKEND_URL': URL})
@patch.dict(os.environ, {'BACKEND_PORT': str(PORT)})
def test_when_only_month_but_not_year_is_specified(tmpdir):
    csv_file_destination_dir = os.path.abspath(tmpdir.mkdir('csv_files'))

    with patch.dict(os.environ, {'CSV_FILE_DIR': csv_file_destination_dir}):
        from export_app import app

        client = TestClient(app)

        response = client.post('/upload?month=10')
        assert response.status_code == 422


@patch.dict(os.environ, {'BACKEND_URL': URL})
@patch.dict(os.environ, {'BACKEND_PORT': str(PORT)})
def test_when_only_year_but_not_month_is_specified(tmpdir):
    csv_file_destination_dir = os.path.abspath(tmpdir.mkdir('csv_files'))

    with patch.dict(os.environ, {'CSV_FILE_DIR': csv_file_destination_dir}):
        from export_app import app

        client = TestClient(app)

        response = client.post('/upload?year=2021')
        assert response.status_code == 422


@patch.dict(os.environ, {'BACKEND_URL': URL})
@patch.dict(os.environ, {'BACKEND_PORT': str(PORT)})
@patch('export_src.utils.get_bucket_id')
@patch('google.cloud.storage.Client')
def test_when_cloud_storage_not_available(storage_client, get_bucket_id, tmpdir):
    csv_file_destination_dir = os.path.abspath(tmpdir.mkdir('csv_files'))

    with patch.dict(os.environ, {'CSV_FILE_DIR': csv_file_destination_dir}):
        from export_app import app

        with patch('os.path.getsize') as os_get_size:
            bucket_mock, object_blob_mock = set_mocks_up(get_bucket_id, os_get_size, storage_client)
            object_blob_mock.upload_from_filename.side_effect = \
                exceptions.ServiceUnavailable('Service unavailable for test reasons')

            client = TestClient(app)

            with requests_mock.Mocker(real_http=True) as m:
                m.get('https://{}:{}/api/v1/sensor'.format(URL, PORT), json=SENSOR_RESPONSE)
                m.get('https://{}:{}/api/v1/station'.format(URL, PORT), json=STATION_RESPONSE)
                m.get('https://{}:{}/api/v1/data'.format(URL, PORT), json=DATA_RESPONSE)
                response = client.post('/upload')
                assert response.status_code == 503
