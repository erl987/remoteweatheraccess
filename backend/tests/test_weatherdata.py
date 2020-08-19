from http import HTTPStatus

import pytest
import pytz
from dateutil.parser import isoparse

# noinspection PyUnresolvedReferences
from .utils import client_without_permissions, client_with_push_user_permissions, client_with_admin_permissions, \
    a_dataset, another_dataset, an_updated_dataset, drop_permissions  # required as a fixture


@pytest.mark.usefixtures('client_with_push_user_permissions', 'a_dataset')
def test_create_dataset(client_with_push_user_permissions, a_dataset):
    result = client_with_push_user_permissions.post('/api/v1/data', json=a_dataset)
    assert result.status_code == HTTPStatus.NO_CONTENT


@pytest.mark.usefixtures('client_with_push_user_permissions', 'a_dataset', 'another_dataset')
def test_create_two_datasets(client_with_push_user_permissions, a_dataset, another_dataset):
    result = client_with_push_user_permissions.post('/api/v1/data', json=a_dataset)
    assert result.status_code == HTTPStatus.NO_CONTENT

    result_2 = client_with_push_user_permissions.post('/api/v1/data', json=another_dataset)
    assert result_2.status_code == HTTPStatus.NO_CONTENT


@pytest.mark.usefixtures('client_with_push_user_permissions', 'a_dataset')
def test_create_same_dataset_twice(client_with_push_user_permissions, a_dataset):
    result = client_with_push_user_permissions.post('/api/v1/data', json=a_dataset)
    assert result.status_code == HTTPStatus.NO_CONTENT

    result_2 = client_with_push_user_permissions.post('/api/v1/data', json=a_dataset)
    assert 'error' in result_2.get_json()
    assert result_2.status_code == HTTPStatus.CONFLICT


@pytest.mark.usefixtures('client_with_push_user_permissions', 'a_dataset')
def test_create_dataset_with_invalid_body(client_with_push_user_permissions, a_dataset):
    invalid_dataset = list(a_dataset)
    del invalid_dataset[0]['pressure']
    invalid_dataset[0]['press'] = 12
    result = client_with_push_user_permissions.post('/api/v1/data', json=invalid_dataset)
    assert 'error' in result.get_json()
    assert result.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.usefixtures('client_with_push_user_permissions')
def test_create_dataset_with_wrong_content_type(client_with_push_user_permissions):
    result = client_with_push_user_permissions.post('/api/v1/data', data={}, content_type='text/html')
    assert 'error' in result.get_json()
    assert result.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.usefixtures('client_without_permissions', 'a_dataset')
def test_create_dataset_without_required_permissions(client_without_permissions, a_dataset):
    result = client_without_permissions.post('/api/v1/data', json=a_dataset)
    assert 'error' in result.get_json()
    assert result.status_code == HTTPStatus.UNAUTHORIZED


@pytest.mark.usefixtures('client_with_admin_permissions', 'a_dataset', 'another_dataset')
def test_delete_dataset(client_with_admin_permissions, a_dataset, another_dataset):
    create_result = client_with_admin_permissions.post('/api/v1/data', json=a_dataset)
    assert create_result.status_code == HTTPStatus.NO_CONTENT
    client_with_admin_permissions.post('/api/v1/data', json=another_dataset)
    delete_payload = {
        'first_timepoint': '2016-02-05T00:00',
        'last_timepoint': '2016-02-07T00:00',
        'stations': ['TES']
    }
    delete_result = client_with_admin_permissions.delete('/api/v1/data', json=delete_payload)
    assert delete_result.status_code == HTTPStatus.NO_CONTENT


@pytest.mark.usefixtures('client_with_admin_permissions')
def test_delete_not_existing_dataset(client_with_admin_permissions):
    delete_payload = {
        'first_timepoint': '2010-01-01T00:00',
        'last_timepoint': '2010-01-31T00:00',
        'stations': ['TES']
    }
    result = client_with_admin_permissions.delete('/api/v1/data', json=delete_payload)
    assert result.status_code == HTTPStatus.NO_CONTENT


@pytest.mark.usefixtures('client_without_permissions')
def test_delete_dataset_without_required_permissions(client_without_permissions):
    delete_payload = {
        'first_timepoint': '2010-01-01T00:00',
        'last_timepoint': '2010-01-31T00:00',
        'stations': ['TES']
    }
    result = client_without_permissions.delete('/api/v1/data', json=delete_payload)
    assert 'error' in result.get_json()
    assert result.status_code == HTTPStatus.UNAUTHORIZED


@pytest.mark.usefixtures('client_with_push_user_permissions', 'a_dataset', 'an_updated_dataset')
def test_update_dataset(client_with_push_user_permissions, a_dataset, an_updated_dataset):
    create_result = client_with_push_user_permissions.post('/api/v1/data', json=a_dataset)
    assert create_result.status_code == HTTPStatus.NO_CONTENT

    update_result = client_with_push_user_permissions.put('/api/v1/data', json=an_updated_dataset)
    assert update_result.status_code == HTTPStatus.NO_CONTENT


@pytest.mark.usefixtures('client_with_push_user_permissions', 'a_dataset', 'another_dataset')
def test_update_dataset_with_time_point_mismatch(client_with_push_user_permissions, a_dataset, another_dataset):
    create_result = client_with_push_user_permissions.post('/api/v1/data', json=a_dataset)
    assert create_result.status_code == HTTPStatus.NO_CONTENT
    update_result = client_with_push_user_permissions.put('/api/v1/data', json=another_dataset[0])
    assert 'error' in update_result.get_json()
    assert update_result.status_code == HTTPStatus.NOT_FOUND


@pytest.mark.usefixtures('client_with_push_user_permissions', 'a_dataset')
def test_update_dataset_with_invalid_body(client_with_push_user_permissions, a_dataset):
    invalid_dataset = list(a_dataset)
    del invalid_dataset[0]['pressure']
    invalid_dataset[0]['press'] = 12
    result = client_with_push_user_permissions.put('/api/v1/data', json=invalid_dataset)
    assert 'error' in result.get_json()
    assert result.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.usefixtures('client_with_push_user_permissions')
def test_update_dataset_with_wrong_content_type(client_with_push_user_permissions):
    result = client_with_push_user_permissions.put('/api/v1/data', data={}, content_type='text/html')
    assert 'error' in result.get_json()
    assert result.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.usefixtures('client_without_permissions', 'an_updated_dataset')
def test_update_dataset_without_required_permissions(client_without_permissions, an_updated_dataset):
    result = client_without_permissions.put('/api/v1/data', json=an_updated_dataset)
    assert 'error' in result.get_json()
    assert result.status_code == HTTPStatus.UNAUTHORIZED


@pytest.mark.usefixtures('client_with_push_user_permissions', 'a_dataset', 'another_dataset')
def test_get_available_time_period(client_with_push_user_permissions, a_dataset, another_dataset):
    client_with_push_user_permissions.post('/api/v1/data', json=a_dataset)
    client_with_push_user_permissions.post('/api/v1/data', json=another_dataset)
    expected_first_timepoint = min(isoparse(a_dataset[0]['timepoint']), isoparse(another_dataset[0]['timepoint']))
    expected_last_timepoint = max(isoparse(a_dataset[0]['timepoint']), isoparse(another_dataset[0]['timepoint']))
    client = drop_permissions(client_with_push_user_permissions)
    result = client.get('/api/v1/data/limits')

    obtained_first_timepoint = isoparse(result.get_json()['first_timepoint'])
    obtained_first_timepoint = obtained_first_timepoint.replace(tzinfo=pytz.UTC)
    obtained_last_timepoint = isoparse(result.get_json()['last_timepoint'])
    obtained_last_timepoint = obtained_last_timepoint.replace(tzinfo=pytz.UTC)

    assert obtained_first_timepoint == expected_first_timepoint
    assert obtained_last_timepoint == expected_last_timepoint
    assert result.status_code == HTTPStatus.OK


@pytest.mark.usefixtures('client_without_permissions')
def test_get_available_time_period_when_empty_database(client_without_permissions):
    result = client_without_permissions.get('/api/v1/data/limits')
    assert result.get_json()['first_timepoint'] is None
    assert result.get_json()['last_timepoint'] is None
    assert result.status_code == HTTPStatus.OK


@pytest.mark.usefixtures('client_with_push_user_permissions', 'a_dataset', 'another_dataset')
def test_get_weather_datasets_only_one(client_with_push_user_permissions, a_dataset, another_dataset):
    a_station_id = a_dataset[0]['station_id']
    a_dataset_create_result = client_with_push_user_permissions.post('/api/v1/data', json=a_dataset)
    assert a_dataset_create_result.status_code == HTTPStatus.NO_CONTENT
    another_dataset_create_result = client_with_push_user_permissions.post('/api/v1/data', json=another_dataset)
    assert another_dataset_create_result.status_code == HTTPStatus.NO_CONTENT
    client = drop_permissions(client_with_push_user_permissions)
    search_result = client.get('/api/v1/data', json={'first_timepoint': a_dataset[0]['timepoint'],
                                                     'last_timepoint': a_dataset[0]['timepoint'],
                                                     'stations': [],
                                                     'sensors': []})
    assert search_result.status_code == HTTPStatus.OK
    assert len(search_result.get_json()[a_station_id]['pressure']) == 1
    assert a_dataset[0]['pressure'] == search_result.get_json()[a_station_id]['pressure'][0]


@pytest.mark.usefixtures('client_with_push_user_permissions', 'a_dataset', 'another_dataset')
def test_get_weather_datasets_all(client_with_push_user_permissions, a_dataset, another_dataset):
    a_station_id = a_dataset[0]['station_id']
    a_dataset_create_result = client_with_push_user_permissions.post('/api/v1/data', json=a_dataset)
    assert a_dataset_create_result.status_code == HTTPStatus.NO_CONTENT
    another_dataset_create_result = client_with_push_user_permissions.post('/api/v1/data', json=another_dataset)
    assert another_dataset_create_result.status_code == HTTPStatus.NO_CONTENT
    client = drop_permissions(client_with_push_user_permissions)
    search_result = client.get('/api/v1/data', json={'first_timepoint': '1900-1-1T00:00',
                                                     'last_timepoint': '2100-1-1T00:00',
                                                     'stations': [],
                                                     'sensors': []})
    assert search_result.status_code == HTTPStatus.OK
    assert len(search_result.get_json()[a_station_id]['pressure']) == 2
    assert a_dataset[0]['pressure'] == search_result.get_json()[a_station_id]['pressure'][0]
    assert another_dataset[0]['pressure'] == search_result.get_json()[a_station_id]['pressure'][1]


@pytest.mark.usefixtures('client_with_push_user_permissions', 'a_dataset', 'another_dataset')
def test_get_weather_datasets_none(client_with_push_user_permissions, a_dataset, another_dataset):
    a_dataset_create_result = client_with_push_user_permissions.post('/api/v1/data', json=a_dataset)
    assert a_dataset_create_result.status_code == HTTPStatus.NO_CONTENT
    another_dataset_create_result = client_with_push_user_permissions.post('/api/v1/data', json=another_dataset)
    assert another_dataset_create_result.status_code == HTTPStatus.NO_CONTENT
    client = drop_permissions(client_with_push_user_permissions)
    search_result = client.get('/api/v1/data', json={'first_timepoint': '2050-1-1T00:00',
                                                     'last_timepoint': '2100-1-1T00:00',
                                                     'stations': [],
                                                     'sensors': []})
    assert search_result.status_code == HTTPStatus.OK
    assert len(search_result.get_json()) == 0


@pytest.mark.usefixtures('client_without_permissions')
def test_get_weather_datasets_with_empty_database(client_without_permissions):
    search_result = client_without_permissions.get('/api/v1/data', json={'first_timepoint': '1900-1-1T00:00',
                                                                         'last_timepoint': '2100-1-1T00:00',
                                                                         'stations': [],
                                                                         'sensors': []})
    assert search_result.status_code == HTTPStatus.OK
    assert len(search_result.get_json()) == 0


@pytest.mark.usefixtures('client_without_permissions')
def test_get_weather_datasets_with_wrong_timepoint_order(client_without_permissions):
    search_result = client_without_permissions.get('/api/v1/data', json={'first_timepoint': '2100-1-1T00:00',
                                                                         'last_timepoint': '1900-1-1T00:00',
                                                                         'stations': [],
                                                                         'sensors': []})
    assert 'error' in search_result.get_json()
    assert search_result.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.usefixtures('client_without_permissions')
def test_get_weather_datasets_with_invalid_parameters(client_without_permissions):
    search_result = client_without_permissions.get('/api/v1/data', json={'first_timepoint': 'invalid',
                                                                         'last_timepoint': '2100-1-1T00:00',
                                                                         'stations': [],
                                                                         'sensors': []})
    assert 'error' in search_result.get_json()
    assert search_result.status_code == HTTPStatus.BAD_REQUEST
