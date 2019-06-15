from http import HTTPStatus

import pytest

from .utils import client_with_admin_permissions, a_user, another_user, an_updated_user,\
    drop_permissions  # required as a fixture


@pytest.mark.usefixtures('client_with_admin_permissions', 'a_user')
def test_create_user(client_with_admin_permissions, a_user):
    result = client_with_admin_permissions.post('/api/v1/user', json=a_user)
    returned_json = result.get_json()
    a_user_with_same_id = dict(a_user)
    del a_user_with_same_id['password']
    a_user_with_same_id['id'] = returned_json['id']
    assert returned_json == a_user_with_same_id
    assert result.status_code == HTTPStatus.CREATED

    location_result = client_with_admin_permissions.get(result.headers['Location'])
    assert location_result.get_json() == returned_json
    assert location_result.status_code == HTTPStatus.OK


@pytest.mark.usefixtures('client_with_admin_permissions', 'a_user')
def test_get_one_user(client_with_admin_permissions, a_user):
    create_result = client_with_admin_permissions.post('/api/v1/user', json=a_user)
    id = create_result.get_json()['id']
    get_result = client_with_admin_permissions.get('/api/v1/user/{}'.format(id))
    a_user_with_same_id = dict(a_user)
    del a_user_with_same_id['password']
    a_user_with_same_id['id'] = id
    assert get_result.get_json() == a_user_with_same_id
    assert get_result.status_code == HTTPStatus.OK


@pytest.mark.usefixtures('client_with_admin_permissions', 'a_user', 'another_user')
def test_users_all(client_with_admin_permissions, a_user, another_user):
    a_user_create_result = client_with_admin_permissions.post('/api/v1/user', json=a_user)
    another_user_create_result = client_with_admin_permissions.post('/api/v1/user', json=another_user)
    search_result = client_with_admin_permissions.get('api/v1/user')
    assert len(search_result.get_json()) == 2
    search_result_ids = set(item['id'] for item in search_result.get_json())
    create_result_ids = set(item['id'] for item in list([a_user_create_result.get_json(),
                                                         another_user_create_result.get_json()]))
    assert search_result_ids == create_result_ids
    assert search_result.status_code == HTTPStatus.OK


@pytest.mark.usefixtures('client_with_admin_permissions', 'a_user', 'an_updated_user')
def test_update_user(client_with_admin_permissions, a_user, an_updated_user):
    create_result = client_with_admin_permissions.post('/api/v1/user', json=a_user)
    id = create_result.get_json()['id']
    update_result = client_with_admin_permissions.put('/api/v1/user/{}'.format(id), json=an_updated_user)
    an_updated_user_with_same_id = dict(an_updated_user)
    an_updated_user_with_same_id['id'] = id
    del an_updated_user_with_same_id['password']
    assert update_result.get_json() == an_updated_user_with_same_id
    assert update_result.status_code == HTTPStatus.OK

    location_result = client_with_admin_permissions.get(update_result.headers['Location'])
    assert location_result.get_json() == update_result.get_json()
    assert location_result.status_code == HTTPStatus.OK


@pytest.mark.usefixtures('client_with_admin_permissions', 'a_user', 'another_user')
def test_delete_user(client_with_admin_permissions, a_user, another_user):
    create_result = client_with_admin_permissions.post('/api/v1/user', json=a_user)
    client_with_admin_permissions.post('/api/v1/user', json=another_user)
    user_id = create_result.get_json()['id']
    delete_result = client_with_admin_permissions.delete('/api/v1/user/{}'.format(user_id))
    assert delete_result.get_json() == create_result.get_json()
    assert delete_result.status_code == HTTPStatus.OK


@pytest.mark.usefixtures('client_with_admin_permissions', 'a_user')
def test_login(client_with_admin_permissions, a_user):
    client_with_admin_permissions.post('/api/v1/user', json=a_user)
    client = drop_permissions(client_with_admin_permissions)
    login_result = client.post('/api/v1/login', json=a_user)
    assert login_result.get_json()['user'] == a_user['name']
    assert len(login_result.get_json()['token']) > 0
    assert login_result.status_code == HTTPStatus.OK
