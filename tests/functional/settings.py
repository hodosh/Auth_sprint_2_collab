from pydantic import BaseSettings, Field


class TestSettings(BaseSettings):
    redis_host: str = Field('127.0.0.1', env='REDIS_HOST')
    redis_port: str = Field('6379', env='REDIS_PORT')

    api_host: str = Field('http://127.0.0.1', env='AUTH_API_HOST')
    api_port: str = Field('5000', env='AUTH_API_PORT')

    db_host: str = Field('127.0.0.1', env='DB_HOST')
    db_port: str = Field('5432', env='DB_PORT')
    db_name: str = Field('auth_database', env='DB_NAME')
    db_user: str = Field('app', env='DB_USER')
    db_pass: str = Field('123qwe', env='DB_PASS')

    jwt_secret_key: str = Field('eyJhbGciOiJSUzI1NiIsImNsYXNzaWQiOjQ5Nn0', env='JWT_SECRET_KEY')
    jwt_algorithms: str = Field('HS256', env='JWT_ALGORITHMS')

    def get_api_url(self):
        return f'{self.api_host}/{self.api_port}'.rstrip('/')


settings = TestSettings()
