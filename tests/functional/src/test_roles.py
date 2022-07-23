import uuid
from http import HTTPStatus

import pytest

from tests.functional.testdata.roles_data import create_role

pytestmark = pytest.mark.asyncio


class TestRoles:

    async def test_get_roles_success(self, make_get_request, actual_token, db_cursor):
        response = await make_get_request('/roles/', headers={'Authorization': f'Bearer {actual_token}'})

        assert response.status == HTTPStatus.OK

        db_cursor.execute(f"SELECT id, name FROM roles;")
        roles = dict(db_cursor.fetchall())

        assert len(response.body) == len(roles)
        for role_id, role_name in roles.items():
            assert {'id': role_id, 'name': role_name} in response.body
        assert response.headers is not None

    async def test_create_role(self, make_post_request, actual_token, db_cursor):
        db_cursor.execute(f"SELECT id FROM permissions;")
        permission_id = db_cursor.fetchone().pop()
        role_unique_name = str(uuid.uuid4())
        data = create_role(name=role_unique_name, permission_id=permission_id)
        response = await make_post_request('/roles/create',
                                           data=data,
                                           headers={'Authorization': f'Bearer {actual_token}'})

        assert response.status == HTTPStatus.OK

        assert list(response.body.keys()) == ['created', 'id', 'name']
        assert response.body['name'] == role_unique_name
        assert response.headers is not None

    async def test_update_role(self, make_post_request, actual_token, db_cursor):
        # prepare role
        db_cursor.execute(f"SELECT id FROM permissions;")
        permission_id = db_cursor.fetchone().pop()
        role_unique_name = str(uuid.uuid4())
        data = create_role(name=role_unique_name, permission_id=permission_id)
        response = await make_post_request('/roles/create',
                                           data=data,
                                           headers={'Authorization': f'Bearer {actual_token}'})

        role_id = response.body['id']

        # update role
        new_role_unique_name = str(uuid.uuid4())
        db_cursor.execute(f"SELECT id FROM permissions where id<>'{permission_id}';")
        new_permission_id = db_cursor.fetchone().pop()
        new_data = create_role(name=new_role_unique_name, permission_id=new_permission_id)
        response = await make_post_request(f'/roles/{role_id}',
                                           data=new_data,
                                           headers={'Authorization': f'Bearer {actual_token}'})

        assert list(response.body.keys()) == ['created', 'id', 'name']
        assert response.body['name'] == new_role_unique_name
        assert response.headers is not None

    async def test_get_role(self, make_get_request, actual_token, db_cursor):
        db_cursor.execute(f"SELECT id, name FROM roles;")
        role_id, role_name = db_cursor.fetchone()
        response = await make_get_request(f'/roles/{role_id}',
                                          headers={'Authorization': f'Bearer {actual_token}'})

        assert list(response.body.keys()) == ['created', 'id', 'name', 'permissions']
        assert response.body['name'] == role_name
        assert response.body['id'] == role_id
        assert isinstance(response.body['permissions'], list)
        assert response.headers is not None

    async def test_delete_role(self, make_post_request, make_delete_request, actual_token, db_cursor):
        # prepare role
        db_cursor.execute(f"SELECT id FROM permissions;")
        permission_id = db_cursor.fetchone().pop()
        role_unique_name = str(uuid.uuid4())
        data = create_role(name=role_unique_name, permission_id=permission_id)
        response = await make_post_request('/roles/create',
                                           data=data,
                                           headers={'Authorization': f'Bearer {actual_token}'})

        role_id = response.body['id']
        # delete role
        response = await make_delete_request(f'/roles/{role_id}',
                                             headers={'Authorization': f'Bearer {actual_token}'})
        assert list(response.body.keys()) == ['created', 'id', 'name']
        assert response.body['name'] == role_unique_name
        assert response.body['id'] == role_id
        assert response.headers is not None
