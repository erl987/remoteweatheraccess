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

import os
from unittest.mock import patch, MagicMock

import pytest
from cacheout import Cache
from google.cloud import storage

from frontend.django_frontend.weatherpage.dash_download_page.callback import update_downloadable_data_callback, \
    download_data_callback
from frontend.django_frontend.weatherpage.dash_download_page.layout import get_layout
from frontend.tests.unit_tests.mocks import StationResponseMock, A_STATION_ID, ANOTHER_STATION_ID


def set_storage_mocks_up(station_id, storage_client):
    object_blob_mock_other = MagicMock(autospec=storage.Blob)
    object_blob_mock_other.name = f'{station_id}/something.txt'

    object_blob_mock_2022 = MagicMock(autospec=storage.Blob)
    object_blob_mock_2022.name = f'{station_id}/EXP05_22.csv'

    object_blob_mock_6_2023 = MagicMock(autospec=storage.Blob)
    object_blob_mock_6_2023.name = f'{station_id}/EXP06_23.csv'

    object_blob_mock_7_2023 = MagicMock(autospec=storage.Blob)
    object_blob_mock_7_2023.name = f'{station_id}/EXP07_23.csv'

    bucket_mock = MagicMock(autospec=storage.Bucket)
    bucket_mock.list_blobs.return_value = [object_blob_mock_other, object_blob_mock_2022, object_blob_mock_6_2023,
                                           object_blob_mock_7_2023]

    storage_client_mock = MagicMock(autospec=storage.Client)
    storage_client_mock.bucket.return_value = bucket_mock

    storage_client.return_value = storage_client_mock

    return bucket_mock


@patch.dict(os.environ, {'TEST_WITH_BUCKET_MOCK': 'True'})
@patch('google.cloud.storage.Client')
def test_get_layout(storage_client, requests_mock):
    requests_mock.get('https://something:443/api/v1/station', json=StationResponseMock.json())

    data_cache = Cache()
    bucket_mock = set_storage_mocks_up(A_STATION_ID, storage_client)
    got_layout = get_layout(data_cache, bucket_mock)

    assert got_layout.children[3].children[0].children[1].children.value == 'Some Place'
    assert got_layout.children[3].children[1].children[1].children.value == 2023


@patch.dict(os.environ, {'TEST_WITH_BUCKET_MOCK': 'True'})
@patch('google.cloud.storage.Client')
def test_get_layout_when_metadata_is_missing(storage_client, requests_mock):
    requests_mock.get('https://something:443/api/v1/station', json=StationResponseMock.json())

    data_cache = Cache()
    bucket_mock = set_storage_mocks_up(ANOTHER_STATION_ID, storage_client)
    with pytest.raises(AssertionError):
        get_layout(data_cache, bucket_mock)


@patch.dict(os.environ, {'TEST_WITH_BUCKET_MOCK': 'True'})
@patch('google.cloud.storage.Client')
def test_update_downloadable_data(storage_client, requests_mock):
    requests_mock.get('https://something:443/api/v1/station', json=StationResponseMock.json())

    data_cache = Cache()
    bucket_mock = set_storage_mocks_up(A_STATION_ID, storage_client)

    component, is_initialize_error = update_downloadable_data_callback('Some Place', 2023, data_cache, bucket_mock)

    assert not is_initialize_error

    assert len(component.children) == 3
    assert len(component.children[0].children) == 4
    assert len(component.children[1].children) == 4
    assert len(component.children[2].children) == 4

    assert component.children[0].children[0].children.disabled
    assert component.children[0].children[1].children.disabled
    assert component.children[0].children[2].children.disabled
    assert component.children[0].children[3].children.disabled

    assert component.children[1].children[0].children.disabled
    assert not component.children[1].children[1].children.disabled
    assert not component.children[1].children[2].children.disabled
    assert component.children[1].children[3].children.disabled

    assert component.children[2].children[0].children.disabled
    assert component.children[2].children[1].children.disabled
    assert component.children[2].children[2].children.disabled
    assert component.children[2].children[3].children.disabled


@patch.dict(os.environ, {'TEST_WITH_BUCKET_MOCK': 'True'})
@patch('google.cloud.storage.Client')
def test_update_downloadable_data_when_invalid_station(storage_client, requests_mock):
    requests_mock.get('https://something:443/api/v1/station', json=StationResponseMock.json())

    data_cache = Cache()
    bucket_mock = set_storage_mocks_up(A_STATION_ID, storage_client)

    component, is_initialize_error = update_downloadable_data_callback('Some Unknown Place', 2023, data_cache,
                                                                       bucket_mock)

    assert is_initialize_error
    assert not component


@patch.dict(os.environ, {'TEST_WITH_BUCKET_MOCK': 'True'})
@patch('google.cloud.storage.Client')
def test_update_downloadable_data_when_no_months_for_that_year(storage_client, requests_mock):
    requests_mock.get('https://something:443/api/v1/station', json=StationResponseMock.json())

    data_cache = Cache()
    bucket_mock = set_storage_mocks_up(A_STATION_ID, storage_client)

    component, is_initialize_error = update_downloadable_data_callback('Some Place', 2021, data_cache, bucket_mock)

    assert not is_initialize_error

    assert len(component.children) == 3
    assert len(component.children[0].children) == 4
    assert len(component.children[1].children) == 4
    assert len(component.children[2].children) == 4

    assert component.children[0].children[0].children.disabled
    assert component.children[0].children[1].children.disabled
    assert component.children[0].children[2].children.disabled
    assert component.children[0].children[3].children.disabled

    assert component.children[1].children[0].children.disabled
    assert component.children[1].children[1].children.disabled
    assert component.children[1].children[2].children.disabled
    assert component.children[1].children[3].children.disabled

    assert component.children[2].children[0].children.disabled
    assert component.children[2].children[1].children.disabled
    assert component.children[2].children[2].children.disabled
    assert component.children[2].children[3].children.disabled


@patch.dict(os.environ, {'TEST_WITH_BUCKET_MOCK': 'True'})
@patch('google.cloud.storage.Client')
def test_download_data(storage_client, requests_mock):
    requests_mock.get('https://something:443/api/v1/station', json=StationResponseMock.json())

    chosen_months_in_year = [False, False, False, False, False, True, False, False, False, False, False, False]

    data_cache = Cache()
    bucket_mock = set_storage_mocks_up(A_STATION_ID, storage_client)

    download_data, is_no_month_selected_warning, is_download_error = \
        download_data_callback(chosen_months_in_year, 'Some Place', 2023, data_cache, bucket_mock)

    assert not is_no_month_selected_warning
    assert not is_download_error
    assert download_data['filename'] == 'EXP06_23.csv'
    assert len(download_data['content']) == 0  # the data is only empty because of the implemented mocking
    assert download_data['type'] == 'text/csv'


@patch.dict(os.environ, {'TEST_WITH_BUCKET_MOCK': 'True'})
@patch('google.cloud.storage.Client')
def test_download_data_when_multiple_months(storage_client, requests_mock):
    requests_mock.get('https://something:443/api/v1/station', json=StationResponseMock.json())

    chosen_months_in_year = [False, False, False, False, False, True, True, False, False, False, False, False]

    data_cache = Cache()
    bucket_mock = set_storage_mocks_up(A_STATION_ID, storage_client)

    download_data, is_no_month_selected_warning, is_download_error = \
        download_data_callback(chosen_months_in_year, 'Some Place', 2023, data_cache, bucket_mock)

    assert not is_no_month_selected_warning
    assert not is_download_error

    assert download_data['base64'] is True
    assert download_data['filename'] == 'weather-data-TES-2023.zip'
    assert download_data['type'] == 'application/zip'


@patch.dict(os.environ, {'TEST_WITH_BUCKET_MOCK': 'True'})
@patch('google.cloud.storage.Client')
def test_download_data_when_no_file(storage_client, requests_mock):
    requests_mock.get('https://something:443/api/v1/station', json=StationResponseMock.json())

    chosen_months_in_year = [False, False, False, False, False, False, False, False, False, False, False, False]

    data_cache = Cache()
    bucket_mock = set_storage_mocks_up(A_STATION_ID, storage_client)

    download_data, is_no_month_selected_warning, is_download_error = \
        download_data_callback(chosen_months_in_year, 'Some Place', 2023, data_cache, bucket_mock)

    assert is_no_month_selected_warning
    assert not is_download_error
    assert not download_data


@patch.dict(os.environ, {'TEST_WITH_BUCKET_MOCK': 'True'})
@patch('google.cloud.storage.Client')
def test_download_data_when_months_without_data(storage_client, requests_mock):
    requests_mock.get('https://something:443/api/v1/station', json=StationResponseMock.json())

    chosen_months_in_year = [True, False, False, False, False, False, False, False, False, False, False, False]

    data_cache = Cache()
    bucket_mock = set_storage_mocks_up(A_STATION_ID, storage_client)

    download_data, is_no_month_selected_warning, is_download_error = \
        download_data_callback(chosen_months_in_year, 'Some Place', 2023, data_cache, bucket_mock)

    assert not is_no_month_selected_warning
    assert is_download_error
    assert not download_data
