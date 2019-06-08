from http import HTTPStatus

import pytest
import dateutil

# noinspection PyUnresolvedReferences
from .utils import client_without_permissions, client_with_user_permissions, a_dataset, another_dataset, \
    an_updated_dataset, drop_permissions  # required as a fixture


@pytest.mark.usefixtures('client_with_user_permissions', 'a_dataset')
def test_create_dataset(client_with_user_permissions, a_dataset):
    result = client_with_user_permissions.post('/api/v1/data', json=a_dataset)
    print(result.get_json())
    returned_json = result.get_json()
    a_dataset_with_same_id = dict(a_dataset)
    a_dataset_with_same_id['id'] = returned_json['id']
    assert returned_json == a_dataset_with_same_id
    assert result.status_code == HTTPStatus.CREATED

    location_result = client_with_user_permissions.get(result.headers['Location'])
    assert location_result.get_json() == returned_json
    assert location_result.status_code == HTTPStatus.OK


@pytest.mark.usefixtures('client_with_user_permissions', 'a_dataset', 'another_dataset')
def test_create_two_datasets(client_with_user_permissions, a_dataset, another_dataset):
    result = client_with_user_permissions.post('/api/v1/data', json=a_dataset)
    assert result.status_code == HTTPStatus.CREATED

    result_2 = client_with_user_permissions.post('/api/v1/data', json=another_dataset)
    assert result_2.status_code == HTTPStatus.CREATED


@pytest.mark.usefixtures('client_with_user_permissions', 'a_dataset', 'another_dataset')
def test_create_same_dataset_twice(client_with_user_permissions, a_dataset, another_dataset):
    result = client_with_user_permissions.post('/api/v1/data', json=a_dataset)
    assert result.status_code == HTTPStatus.CREATED

    result_2 = client_with_user_permissions.post('/api/v1/data', json=a_dataset)
    assert 'error' in result_2.get_json()
    assert result_2.status_code == HTTPStatus.CONFLICT


@pytest.mark.usefixtures('client_with_user_permissions', 'a_dataset')
def test_create_dataset_with_invalid_body(client_with_user_permissions, a_dataset):
    invalid_dataset = dict(a_dataset)
    del invalid_dataset['humidity']
    invalid_dataset['humid'] = 12
    result = client_with_user_permissions.post('/api/v1/data', json=invalid_dataset)
    assert 'error' in result.get_json()
    assert result.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.usefixtures('client_with_user_permissions', 'a_dataset')
def test_create_dataset_with_wrong_content_type(client_with_user_permissions):
    result = client_with_user_permissions.post('/api/v1/data', data={}, content_type='text/html')
    assert 'error' in result.get_json()
    assert result.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.usefixtures('client_without_permissions', 'a_dataset')
def test_create_dataset_without_required_permissions(client_without_permissions, a_dataset):
    result = client_without_permissions.post('/api/v1/data', json=a_dataset)
    assert 'error' in result.get_json()
    assert result.status_code == HTTPStatus.UNAUTHORIZED


@pytest.mark.usefixtures('client_with_user_permissions', 'a_dataset', 'another_dataset')
def test_delete_dataset(client_with_user_permissions, a_dataset, another_dataset):
    create_result = client_with_user_permissions.post('/api/v1/data', json=a_dataset)
    client_with_user_permissions.post('/api/v1/data', json=another_dataset)
    dataset_id = create_result.get_json()['id']
    delete_result = client_with_user_permissions.delete('/api/v1/data/{}'.format(dataset_id))
    assert delete_result.get_json() == create_result.get_json()
    assert delete_result.status_code == HTTPStatus.OK


@pytest.mark.usefixtures('client_with_user_permissions', 'a_dataset')
def test_delete_not_existing_dataset(client_with_user_permissions, a_dataset):
    result = client_with_user_permissions.delete('/api/v1/data/1')
    assert len(result.data) == 0  # no JSON, as the body is empty
    assert result.status_code == HTTPStatus.NO_CONTENT


@pytest.mark.usefixtures('client_without_permissions', 'a_dataset')
def test_delete_dataset_without_required_permissions(client_without_permissions, a_dataset):
    result = client_without_permissions.delete('/api/v1/data/1')
    assert 'error' in result.get_json()
    assert result.status_code == HTTPStatus.UNAUTHORIZED


@pytest.mark.usefixtures('client_with_user_permissions', 'a_dataset', 'an_updated_dataset')
def test_update_dataset(client_with_user_permissions, a_dataset, an_updated_dataset):
    create_result = client_with_user_permissions.post('/api/v1/data', json=a_dataset)
    id = create_result.get_json()['id']
    update_result = client_with_user_permissions.put('/api/v1/data/{}'.format(id), json=an_updated_dataset)
    an_updated_dataset_with_same_id = dict(an_updated_dataset)
    an_updated_dataset_with_same_id['id'] = id
    assert update_result.get_json() == an_updated_dataset_with_same_id
    assert update_result.status_code == HTTPStatus.OK

    location_result = client_with_user_permissions.get(update_result.headers['Location'])
    assert location_result.get_json() == update_result.get_json()
    assert location_result.status_code == HTTPStatus.OK


@pytest.mark.usefixtures('client_with_user_permissions', 'a_dataset', 'an_updated_dataset')
def test_update_dataset_when_not_existing(client_with_user_permissions, an_updated_dataset):
    update_result = client_with_user_permissions.put('/api/v1/data/1', json=an_updated_dataset)
    assert 'error' in update_result.get_json()
    assert update_result.status_code == HTTPStatus.NOT_FOUND


@pytest.mark.usefixtures('client_with_user_permissions', 'a_dataset', 'another_dataset')
def test_update_dataset_with_time_point_mismatch(client_with_user_permissions, a_dataset, another_dataset):
    create_result = client_with_user_permissions.post('/api/v1/data', json=a_dataset)
    id = create_result.get_json()['id']
    update_result = client_with_user_permissions.put('/api/v1/data/{}'.format(id), json=another_dataset)
    assert 'error' in update_result.get_json()
    assert update_result.status_code == HTTPStatus.CONFLICT


@pytest.mark.usefixtures('client_with_user_permissions', 'a_dataset')
def test_update_dataset_with_invalid_body(client_with_user_permissions, a_dataset):
    invalid_dataset = dict(a_dataset)
    del invalid_dataset['humidity']
    invalid_dataset['humid'] = 12
    result = client_with_user_permissions.put('/api/v1/data/1', json=invalid_dataset)
    assert 'error' in result.get_json()
    assert result.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.usefixtures('client_with_user_permissions', 'a_dataset')
def test_update_dataset_with_wrong_content_type(client_with_user_permissions):
    result = client_with_user_permissions.put('/api/v1/data/1', data={}, content_type='text/html')
    assert 'error' in result.get_json()
    assert result.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.usefixtures('client_without_permissions', 'an_updated_dataset')
def test_update_dataset_without_required_permissions(client_without_permissions, an_updated_dataset):
    result = client_without_permissions.put('/api/v1/data/1', json=an_updated_dataset)
    assert 'error' in result.get_json()
    assert result.status_code == HTTPStatus.UNAUTHORIZED


@pytest.mark.usefixtures('client_with_user_permissions', 'a_dataset')
def test_get_one_weather_dataset(client_with_user_permissions, a_dataset):
    create_result = client_with_user_permissions.post('/api/v1/data', json=a_dataset)
    id = create_result.get_json()['id']
    client = drop_permissions(client_with_user_permissions)
    get_result = client.get('/api/v1/data/{}'.format(id))
    a_dataset_with_same_id = dict(a_dataset)
    a_dataset_with_same_id['id'] = id
    assert get_result.get_json() == a_dataset_with_same_id
    assert get_result.status_code == HTTPStatus.OK


@pytest.mark.usefixtures('client_without_permissions', 'a_dataset')
def test_get_one_dataset_that_does_not_exist(client_without_permissions):
    result = client_without_permissions.get('/api/v1/data/1')
    assert 'error' in result.get_json()
    assert result.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.usefixtures('client_with_user_permissions', 'a_dataset', 'another_dataset')
def test_get_available_time_period(client_with_user_permissions, a_dataset, another_dataset):
    client_with_user_permissions.post('/api/v1/data', json=a_dataset)
    client_with_user_permissions.post('/api/v1/data', json=another_dataset)
    first = min(dateutil.parser.parse(a_dataset['timepoint']), dateutil.parser.parse(another_dataset['timepoint']))
    last = max(dateutil.parser.parse(a_dataset['timepoint']), dateutil.parser.parse(another_dataset['timepoint']))
    client = drop_permissions(client_with_user_permissions)
    result = client.get('/api/v1/data/limits')
    assert dateutil.parser.parse(result.get_json()['first']) == first
    assert dateutil.parser.parse(result.get_json()['last']) == last
    assert result.status_code == HTTPStatus.OK


@pytest.mark.usefixtures('client_without_permissions')
def test_get_available_time_period_when_empty_database(client_without_permissions):
    result = client_without_permissions.get('/api/v1/data/limits')
    assert 'error' in result.get_json()
    assert result.status_code == HTTPStatus.NOT_FOUND


@pytest.mark.usefixtures('client_with_user_permissions', 'a_dataset', 'another_dataset')
def test_get_weather_datasets_only_one(client_with_user_permissions, a_dataset, another_dataset):
    a_dataset_create_result = client_with_user_permissions.post('/api/v1/data', json=a_dataset)
    client_with_user_permissions.post('/api/v1/data', json=another_dataset)
    client = drop_permissions(client_with_user_permissions)
    search_result = client.get('api/v1/data', query_string={'first': a_dataset['timepoint'],
                                                            'last': a_dataset['timepoint']})
    assert len(search_result.get_json()) == 1
    a_dataset_with_same_id = dict(a_dataset)
    a_dataset_with_same_id['id'] = a_dataset_create_result.get_json()['id']
    assert search_result.get_json()[0] == a_dataset_with_same_id
    assert search_result.status_code == HTTPStatus.OK


@pytest.mark.usefixtures('client_with_user_permissions', 'a_dataset', 'another_dataset')
def test_get_weather_datasets_all(client_with_user_permissions, a_dataset, another_dataset):
    a_dataset_create_result = client_with_user_permissions.post('/api/v1/data', json=a_dataset)
    another_dataset_create_result = client_with_user_permissions.post('/api/v1/data', json=another_dataset)
    client = drop_permissions(client_with_user_permissions)
    search_result = client.get('api/v1/data', query_string={'first': '1900-1-1T00:00',
                                                            'last': '2100-1-1T00:00'})
    assert len(search_result.get_json()) == 2
    search_result_ids = set(item['id'] for item in search_result.get_json())
    create_result_ids = set(item['id'] for item in list([a_dataset_create_result.get_json(),
                                                         another_dataset_create_result.get_json()]))
    assert search_result_ids == create_result_ids
    assert search_result.status_code == HTTPStatus.OK


@pytest.mark.usefixtures('client_with_user_permissions', 'a_dataset', 'another_dataset')
def test_get_weather_datasets_none(client_with_user_permissions, a_dataset, another_dataset):
    client_with_user_permissions.post('/api/v1/data', json=a_dataset)
    client_with_user_permissions.post('/api/v1/data', json=another_dataset)
    client = drop_permissions(client_with_user_permissions)
    search_result = client.get('api/v1/data', query_string={'first': '2050-1-1T00:00',
                                                            'last': '2100-1-1T00:00'})
    assert len(search_result.get_json()) == 0
    assert search_result.status_code == HTTPStatus.OK


@pytest.mark.usefixtures('client_without_permissions')
def test_get_weather_datasets_with_empty_database(client_without_permissions):
    search_result = client_without_permissions.get('api/v1/data', query_string={'first': '1900-1-1T00:00',
                                                                                'last': '2100-1-1T00:00'})
    assert len(search_result.get_json()) == 0
    assert search_result.status_code == HTTPStatus.OK


@pytest.mark.usefixtures('client_without_permissions')
def test_get_weather_datasets_with_wrong_timepoint_order(client_without_permissions):
    search_result = client_without_permissions.get('api/v1/data', query_string={'first': '2100-1-1T00:00',
                                                                                'last': '1900-1-1T00:00'})
    assert 'error' in search_result.get_json()
    assert search_result.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.usefixtures('client_without_permissions')
def test_get_weather_datasets_with_invalid_parameters(client_without_permissions):
    search_result = client_without_permissions.get('api/v1/data', query_string={'first': 'invalid',
                                                                                'last': '2100-1-1T00:00'})
    assert 'error' in search_result.get_json()
    assert search_result.status_code == HTTPStatus.BAD_REQUEST
