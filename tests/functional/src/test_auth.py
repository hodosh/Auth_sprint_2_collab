from http import HTTPStatus

import jwt
import pytest

from tests.functional.settings import settings
from tests.functional.testdata.auth_data import (
    login_data,
    login_wrong_email_data,
    login_wrong_password_data,
)

pytestmark = pytest.mark.asyncio


class TestAuth:

    async def test_login_success(self, make_post_request):
        response = await make_post_request('/auth/login',
                                           data=login_data)

        assert response.status == HTTPStatus.OK
        assert list(response.body.keys()) == ['token']
        assert response.headers is not None

    async def test_login_no_data_fail(self, make_post_request):
        response = await make_post_request('/auth/login',
                                           data={})
        assert response.status == HTTPStatus.EXPECTATION_FAILED
        assert response.body['description'] == 'cannot find email and password in data!'

    async def test_login_wrong_username_fail(self, make_post_request):
        response = await make_post_request('/auth/login',
                                           data=login_wrong_email_data)
        assert response.status == HTTPStatus.NOT_FOUND
        assert response.body['description'] == f'user with email={login_wrong_email_data["email"]} not found'

    async def test_login_wrong_password_fail(self, make_post_request):
        response = await make_post_request('/auth/login',
                                           data=login_wrong_password_data)
        assert response.status == HTTPStatus.EXPECTATION_FAILED
        assert response.body['description'] == 'password is incorrect'

    async def test_logout_success(self, make_delete_request, actual_token, redis_client):
        response = await make_delete_request('/auth/logout',
                                             headers={'Authorization': f'Bearer {actual_token}'})

        assert response.status == HTTPStatus.OK
        assert response.body['message'] == 'Access token revoked'

        # проверяем, что в редис появилась запись
        res = jwt.decode(actual_token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithms])
        assert redis_client.get(res['jti'])

    async def test_logout_fail(self, make_delete_request, actual_token, redis_client):
        response = await make_delete_request('/auth/logout',
                                             headers={})

        assert response.status == HTTPStatus.UNAUTHORIZED
        assert response.body['msg'] == 'Missing Authorization Header'

    async def test_bad_token_fail(self, make_delete_request, make_post_request, actual_token):
        await make_delete_request('/auth/logout',
                                  headers={'Authorization': f'Bearer {actual_token}'})

        response = await make_delete_request('/auth/logout',
                                             headers={'Authorization': f'Bearer {actual_token}'})

        assert response.status == HTTPStatus.UNAUTHORIZED
        assert response.body['msg'] == 'Token has been revoked'
