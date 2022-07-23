from http import HTTPStatus

import pytest

from tests.functional.testdata.auth_data import login_data
from tests.functional.testdata.users_data import (
    register_data, passwords_mismatch_data, register_base_data, update_user_data,
)

pytestmark = pytest.mark.asyncio


class TestUsers:

    async def test_register_success(self, make_post_request):
        response = await make_post_request('/users/register',
                                           data=register_data)

        assert response.status == HTTPStatus.CREATED
        assert response.body['disabled'] is False
        assert response.body['email'] == register_data['email']
        assert response.headers is not None

    async def test_register_no_data_fail(self, make_post_request):
        response = await make_post_request('/users/register',
                                           data={})

        assert response.status == HTTPStatus.EXPECTATION_FAILED
        assert response.body['description'] == 'cannot find email, password and password_confirm in data!'
        assert response.headers is not None

    async def test_register_passwords_mismatch_fail(self, make_post_request):
        response = await make_post_request('/users/register',
                                           data=passwords_mismatch_data)

        assert response.status == HTTPStatus.EXPECTATION_FAILED
        assert response.body['description'] == 'passwords do not match'
        assert response.headers is not None

    async def test_register_user_exists_fail(self, make_post_request, actual_token):
        await make_post_request('/users/register',
                                data=register_base_data)
        response = await make_post_request('/users/register',
                                           data=register_base_data)
        assert response.status == HTTPStatus.EXPECTATION_FAILED
        assert response.body['description'] == f'user with email={register_base_data["email"]} exists'
        assert response.headers is not None

    async def test_get_users_success(self, make_get_request, actual_token):
        response = await make_get_request('/users/', headers={'Authorization': f'Bearer {actual_token}'})

        assert response.status == HTTPStatus.OK

        assert isinstance(response.body, list)
        assert list(response.body.pop().keys()) == ['disabled', 'email', 'id']
        assert response.headers is not None

    async def test_get_user_success(self, make_get_request, actual_token, db_cursor):
        db_cursor.execute("SELECT id, email, disabled FROM users;")
        user_id, email, disabled = db_cursor.fetchone()
        response = await make_get_request(f'/users/{user_id}', headers={'Authorization': f'Bearer {actual_token}'})

        assert response.status == HTTPStatus.OK
        assert response.body == {'disabled': disabled,
                                 'email': email,
                                 'id': user_id}
        assert response.headers is not None

    async def test_get_user_role(self, make_get_request, actual_token, db_cursor):
        db_cursor.execute(f"SELECT id, role_id FROM users where email='{login_data['email']}';")
        user_id, role_id = db_cursor.fetchone()
        response = await make_get_request(f'/users/{user_id}/role', headers={'Authorization': f'Bearer {actual_token}'})

        assert response.status == HTTPStatus.OK
        assert list(response.body.keys()) == ['name', 'permissions']
        db_cursor.execute(f"SELECT name FROM roles where id='{role_id}';")
        role_name = db_cursor.fetchone().pop()
        assert response.body['name'] == role_name
        assert response.headers is not None

    async def test_update_user(self, make_post_request, actual_token):
        response = await make_post_request('/users/register',
                                           data=register_data)
        user_id = response.body['id']
        response = await make_post_request(f'/users/{user_id}',
                                           data=update_user_data,
                                           headers={'Authorization': f'Bearer {actual_token}'})
        assert response.body['id'] == user_id

    async def test_disable_user(self, make_post_request, make_delete_request, actual_token, db_cursor):
        response = await make_post_request('/users/register',
                                           data=register_data)
        user_id = response.body['id']
        response = await make_delete_request(f'/users/{user_id}',
                                             headers={'Authorization': f'Bearer {actual_token}'})
        assert response.body['id'] == user_id
        assert response.body['disabled'] is True
        db_cursor.execute(f"SELECT disabled FROM users where id='{user_id}';")
        status = db_cursor.fetchone().pop()
        assert status is True

    async def test_set_user_role(self, make_post_request, make_put_request, actual_token, db_cursor):
        response = await make_post_request('/users/register',
                                           data=register_data)
        user_id = response.body['id']
        db_cursor.execute(f"SELECT role_id FROM users where id='{user_id}';")
        user_role_id = db_cursor.fetchone().pop()
        db_cursor.execute(f"SELECT id FROM roles where id<>'{user_role_id}';")
        new_role_id = db_cursor.fetchone().pop()
        response = await make_put_request(f'/users/{user_id}/role/{new_role_id}',
                                          headers={'Authorization': f'Bearer {actual_token}'})
        assert response.body['role_id'] != user_role_id
        assert response.body['role_id'] == new_role_id

    async def test_get_user_history(self, make_get_request, actual_token, db_cursor):
        db_cursor.execute(f"SELECT id FROM users where email='{login_data['email']}';")
        user_id = db_cursor.fetchone().pop()
        response = await make_get_request(f'/users/{user_id}/history',
                                          headers={'Authorization': f'Bearer {actual_token}'})

        assert list(response.body.keys()) == ['history', 'page', 'per_page']
        assert isinstance(response.body['history'], list)
        assert list(response.body['history'][0].keys()) == ['activity', 'created']
