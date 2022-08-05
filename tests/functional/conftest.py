import asyncio
import json
import typing as t
from dataclasses import dataclass

import aiohttp
import aioredis
import psycopg2
import pytest
from multidict import CIMultiDictProxy
from psycopg2.extras import DictCursor

from tests.functional.settings import settings
from tests.functional.testdata.auth_data import (
    login_data,
    super_user_role_name,
)

DSL = {
    'dbname': settings.db_name,
    'user': settings.db_user,
    'password': settings.db_pass,
    'host': settings.db_host,
    'port': settings.db_port,
}


@dataclass
class HTTPResponse:
    body: dict
    headers: CIMultiDictProxy[str]
    status: int


@pytest.fixture(scope='session')
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope='session')
async def session():
    connector = aiohttp.TCPConnector(force_close=True)
    session = aiohttp.ClientSession(connector=connector)
    yield session
    await session.close()


@pytest.fixture(scope='function')
def make_get_request():
    async def inner(method: str, headers: dict = {}) -> HTTPResponse:
        headers = {'Content-Type': 'application/json', **headers}
        url = f'{settings.api_host.rstrip("/")}:{settings.api_port}/api/v1{method}'
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(url) as response:
                return HTTPResponse(
                    body=await response.json(),
                    headers=response.headers,
                    status=response.status,
                )

    return inner


@pytest.fixture(scope='function')
def make_post_request():
    async def inner(method: str, data: t.Optional[dict] = None, headers={}) -> HTTPResponse:
        headers = {'Content-Type': 'application/json', **headers}
        data = data or {}
        url = f'{settings.api_host.rstrip("/")}:{settings.api_port}/api/v1{method}'
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.post(url, data=json.dumps(data)) as response:
                return HTTPResponse(
                    body=await response.json(),
                    headers=response.headers,
                    status=response.status,
                )

    return inner


@pytest.fixture(scope='function')
def make_put_request():
    async def inner(method: str, data: t.Optional[dict] = None, headers={}) -> HTTPResponse:
        headers = {'Content-Type': 'application/json', **headers}
        data = data or {}
        url = f'{settings.api_host.rstrip("/")}:{settings.api_port}/api/v1{method}'
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.put(url, data=json.dumps(data)) as response:
                return HTTPResponse(
                    body=await response.json(),
                    headers=response.headers,
                    status=response.status,
                )

    return inner


@pytest.fixture(scope='function')
def make_delete_request():
    async def inner(method: str, data: t.Optional[dict] = None, headers: dict = {}) -> HTTPResponse:
        headers = {'Content-Type': 'application/json', **headers}
        data = data or {}
        url = f'{settings.api_host.rstrip("/")}:{settings.api_port}/api/v1{method}'
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.delete(url, data=json.dumps(data)) as response:
                return HTTPResponse(
                    body=await response.json(),
                    headers=response.headers,
                    status=response.status,
                )

    return inner


@pytest.fixture(scope='session')
def db_connection():
    conn = psycopg2.connect(**DSL, cursor_factory=DictCursor)
    yield conn
    conn.close()


@pytest.fixture(scope='function')
def db_cursor(db_connection):
    cursor = db_connection.cursor()
    yield cursor
    cursor.close()


@pytest.fixture(scope='function')
async def actual_token(make_post_request, db_cursor, db_connection):
    await make_post_request('/users/register',
                            data=login_data)
    db_cursor.execute(f"SELECT id FROM roles WHERE name='{super_user_role_name}';")
    role_id = db_cursor.fetchone().pop()

    db_cursor.execute(f"SELECT id FROM users WHERE email='{login_data['email']}';")
    user_id = db_cursor.fetchone().pop()

    db_cursor.execute(f"UPDATE users SET role_id='{role_id}' WHERE id='{user_id}';")
    db_connection.commit()

    response = await make_post_request('/auth/login',
                                       data=login_data)
    yield response.body['token']


@pytest.fixture(scope='session')
async def redis_client():
    client = await aioredis.create_redis_pool((settings.redis_host, settings.redis_port), minsize=10, maxsize=20)
    yield client
    client.close()


@pytest.fixture(scope='function')
def read_from_redis():
    async def inner(key: t.Union[str, bytes]):
        redis = await aioredis.create_redis_pool((settings.redis_host, settings.redis_port), minsize=10, maxsize=20)

        return await redis.get(key)

    return inner


@pytest.fixture(scope='function')
def put_to_redis():
    async def inner(key: t.Union[str, bytes], data: t.Dict[t.AnyStr, t.Any]):
        redis = await aioredis.create_redis_pool((settings.redis_host, settings.redis_port), minsize=10, maxsize=20)
        await redis.set(key, json.dumps(data), expire=60)

    return inner
