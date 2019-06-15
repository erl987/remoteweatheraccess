from http import HTTPStatus

import pytest

from .utils import client_with_admin_permissions, client_with_push_user_permissions, client_without_permissions, \
    a_user, another_user, an_updated_user, drop_permissions  # required as a fixture


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


@pytest.mark.usefixtures('client_with_admin_permissions', 'a_user', 'another_user')
def test_create_two_users(client_with_admin_permissions, a_user, another_user):
    result = client_with_admin_permissions.post('/api/v1/user', json=a_user)
    assert result.status_code == HTTPStatus.CREATED

    result_2 = client_with_admin_permissions.post('/api/v1/user', json=another_user)
    assert result_2.status_code == HTTPStatus.CREATED


@pytest.mark.usefixtures('client_with_admin_permissions', 'a_user')
def test_create_same_user_twice(client_with_admin_permissions, a_user):
    result = client_with_admin_permissions.post('/api/v1/user', json=a_user)
    assert result.status_code == HTTPStatus.CREATED

    result_2 = client_with_admin_permissions.post('/api/v1/user', json=a_user)
    assert 'error' in result_2.get_json()
    assert result_2.status_code == HTTPStatus.CONFLICT


@pytest.mark.usefixtures('client_with_admin_permissions', 'a_user')
def test_create_user_with_invalid_body(client_with_admin_permissions, a_user):
    invalid_user = dict(a_user)
    del invalid_user['name']
    result = client_with_admin_permissions.post('/api/v1/user', json=invalid_user)
    assert 'error' in result.get_json()
    assert result.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.usefixtures('client_with_admin_permissions')
def test_create_user_with_wrong_content_type(client_with_admin_permissions):
    result = client_with_admin_permissions.post('/api/v1/user', data={}, content_type='text/html')
    assert 'error' in result.get_json()
    assert result.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.usefixtures('client_without_permissions', 'a_user')
def test_create_dataset_without_required_permissions(client_without_permissions, a_user):
    result = client_without_permissions.post('/api/v1/user', json=a_user)
    assert 'error' in result.get_json()
    assert result.status_code == HTTPStatus.UNAUTHORIZED


@pytest.mark.usefixtures('client_with_push_user_permissions', 'a_user')
def test_create_dataset_with_insufficient_permissions(client_with_push_user_permissions, a_user):
    result = client_with_push_user_permissions.post('/api/v1/user', json=a_user)
    assert 'error' in result.get_json()
    assert result.status_code == HTTPStatus.FORBIDDEN


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


@pytest.mark.usefixtures('client_with_admin_permissions')
def test_get_one_user_that_does_not_exist(client_with_admin_permissions):
    result = client_with_admin_permissions.get('/api/v1/user/1')
    assert 'error' in result.get_json()
    assert result.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.usefixtures('client_with_admin_permissions')
def test_get_one_user_with_invalid_id(client_with_admin_permissions):
    result = client_with_admin_permissions.get('/api/v1/user/letters')
    assert 'error' in result.get_json()
    assert result.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.usefixtures('client_without_permissions')
def test_get_one_user_without_required_permissions(client_without_permissions):
    result = client_without_permissions.get('/api/v1/user/1')
    assert 'error' in result.get_json()
    assert result.status_code == HTTPStatus.UNAUTHORIZED


@pytest.mark.usefixtures('client_with_push_user_permissions')
def test_get_one_user_with_insufficient_permissions(client_with_push_user_permissions):
    result = client_with_push_user_permissions.get('/api/v1/user/1')
    assert 'error' in result.get_json()
    assert result.status_code == HTTPStatus.FORBIDDEN


@pytest.mark.usefixtures('client_with_admin_permissions', 'a_user', 'another_user')
def test_get_all_users(client_with_admin_permissions, a_user, another_user):
    a_user_create_result = client_with_admin_permissions.post('/api/v1/user', json=a_user)
    another_user_create_result = client_with_admin_permissions.post('/api/v1/user', json=another_user)
    search_result = client_with_admin_permissions.get('api/v1/user')
    assert len(search_result.get_json()) == 2
    search_result_ids = set(item['id'] for item in search_result.get_json())
    create_result_ids = set(item['id'] for item in list([a_user_create_result.get_json(),
                                                         another_user_create_result.get_json()]))
    assert search_result_ids == create_result_ids
    assert search_result.status_code == HTTPStatus.OK


@pytest.mark.usefixtures('client_with_admin_permissions')
def test_get_all_users_when_empty_list(client_with_admin_permissions):
    search_result = client_with_admin_permissions.get('api/v1/user')
    assert len(search_result.get_json()) == 0
    assert search_result.status_code == HTTPStatus.OK


@pytest.mark.usefixtures('client_without_permissions')
def test_get_all_users_without_required_permissions(client_without_permissions):
    result = client_without_permissions.get('/api/v1/user')
    assert 'error' in result.get_json()
    assert result.status_code == HTTPStatus.UNAUTHORIZED


@pytest.mark.usefixtures('client_with_push_user_permissions')
def test_get_all_users_with_insufficient_permissions(client_with_push_user_permissions):
    result = client_with_push_user_permissions.get('/api/v1/user')
    assert 'error' in result.get_json()
    assert result.status_code == HTTPStatus.FORBIDDEN


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


@pytest.mark.usefixtures('client_with_admin_permissions', 'an_updated_user')
def test_update_user_when_not_existing(client_with_admin_permissions, an_updated_user):
    update_result = client_with_admin_permissions.put('/api/v1/user/1', json=an_updated_user)
    assert 'error' in update_result.get_json()
    assert update_result.status_code == HTTPStatus.NOT_FOUND


@pytest.mark.usefixtures('client_with_admin_permissions', 'a_user', 'another_user')
def test_update_user_with_mismatch_of_details(client_with_admin_permissions, a_user, another_user):
    create_result = client_with_admin_permissions.post('/api/v1/user', json=a_user)
    id = create_result.get_json()['id']
    update_result = client_with_admin_permissions.put('/api/v1/user/{}'.format(id), json=another_user)
    assert 'error' in update_result.get_json()
    assert update_result.status_code == HTTPStatus.CONFLICT


@pytest.mark.usefixtures('client_with_admin_permissions', 'a_user')
def test_update_user_with_invalid_body(client_with_admin_permissions, a_user):
    invalid_user = dict(a_user)
    del invalid_user['name']
    result = client_with_admin_permissions.put('/api/v1/user/1', json=invalid_user)
    assert 'error' in result.get_json()
    assert result.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.usefixtures('client_with_admin_permissions')
def test_update_user_with_wrong_content_type(client_with_admin_permissions):
    result = client_with_admin_permissions.put('/api/v1/user/1', data={}, content_type='text/html')
    assert 'error' in result.get_json()
    assert result.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.usefixtures('client_without_permissions', 'a_user')
def test_update_user_without_required_permissions(client_without_permissions, a_user):
    result = client_without_permissions.put('/api/v1/user/1', json=a_user)
    assert 'error' in result.get_json()
    assert result.status_code == HTTPStatus.UNAUTHORIZED


@pytest.mark.usefixtures('client_with_push_user_permissions', 'a_user')
def test_update_user_with_insufficient_permissions(client_with_push_user_permissions, a_user):
    result = client_with_push_user_permissions.put('/api/v1/user/1', json=a_user)
    assert 'error' in result.get_json()
    assert result.status_code == HTTPStatus.FORBIDDEN


@pytest.mark.usefixtures('client_with_admin_permissions', 'a_user', 'another_user')
def test_delete_user(client_with_admin_permissions, a_user, another_user):
    create_result = client_with_admin_permissions.post('/api/v1/user', json=a_user)
    client_with_admin_permissions.post('/api/v1/user', json=another_user)
    user_id = create_result.get_json()['id']
    delete_result = client_with_admin_permissions.delete('/api/v1/user/{}'.format(user_id))
    assert delete_result.get_json() == create_result.get_json()
    assert delete_result.status_code == HTTPStatus.OK


@pytest.mark.usefixtures('client_with_admin_permissions')
def test_delete_not_existing_user(client_with_admin_permissions):
    result = client_with_admin_permissions.delete('/api/v1/user/1')
    assert len(result.data) == 0  # no JSON, as the body is empty
    assert result.status_code == HTTPStatus.NO_CONTENT


@pytest.mark.usefixtures('client_without_permissions')
def test_delete_user_without_required_permissions(client_without_permissions):
    result = client_without_permissions.delete('/api/v1/user/1')
    assert 'error' in result.get_json()
    assert result.status_code == HTTPStatus.UNAUTHORIZED


@pytest.mark.usefixtures('client_with_push_user_permissions')
def test_delete_user_with_insufficient_permissions(client_with_push_user_permissions):
    result = client_with_push_user_permissions.put('/api/v1/user/1')
    assert 'error' in result.get_json()
    assert result.status_code == HTTPStatus.FORBIDDEN


@pytest.mark.usefixtures('client_with_admin_permissions', 'a_user')
def test_login(client_with_admin_permissions, a_user):
    client_with_admin_permissions.post('/api/v1/user', json=a_user)
    client = drop_permissions(client_with_admin_permissions)
    login_result = client.post('/api/v1/login', json=a_user)
    assert login_result.get_json()['user'] == a_user['name']
    assert len(login_result.get_json()['token']) > 0
    assert login_result.status_code == HTTPStatus.OK


@pytest.mark.usefixtures('client_without_permissions', 'a_user')
def test_login_with_invalid_body(client_without_permissions, a_user):
    invalid_user = dict(a_user)
    del invalid_user['name']
    result = client_without_permissions.post('/api/v1/login', json=invalid_user)
    assert 'error' in result.get_json()
    assert result.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.usefixtures('client_without_permissions')
def test_login_with_wrong_content_type(client_without_permissions):
    result = client_without_permissions.post('/api/v1/login', data={}, content_type='text/html')
    assert 'error' in result.get_json()
    assert result.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.usefixtures('client_with_admin_permissions', 'a_user', 'another_user')
def test_login_with_wrong_user(client_with_admin_permissions, a_user, another_user):
    client_with_admin_permissions.post('/api/v1/user', json=a_user)
    client = drop_permissions(client_with_admin_permissions)
    login_result = client.post('/api/v1/login', json=another_user)
    assert 'error' in login_result.get_json()
    assert login_result.status_code == HTTPStatus.UNAUTHORIZED


@pytest.mark.usefixtures('client_with_admin_permissions', 'a_user')
def test_login_with_wrong_password(client_with_admin_permissions, a_user):
    client_with_admin_permissions.post('/api/v1/user', json=a_user)
    client = drop_permissions(client_with_admin_permissions)
    user_with_invalid_password = dict(a_user)
    user_with_invalid_password['password'] = 'something'
    login_result = client.post('/api/v1/login', json=user_with_invalid_password)
    assert 'error' in login_result.get_json()
    assert login_result.status_code == HTTPStatus.UNAUTHORIZED
