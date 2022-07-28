import os

from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    # Название проекта. Используется в Swagger-документации
    PROJECT_NAME = 'auth_service'

    # Корень проекта
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    # Database path
    DB_USER = Field(env='DB_USER', default='app')
    DB_PASS = Field(env='DB_PASS', default='123qwe')
    DB_HOST = Field(env='DB_HOST', default='127.0.0.1')

    DB_NAME = Field(env='DB_NAME', default='auth_database')
    DB_TEST_NAME = Field(env='DB_TEST_NAME', default='auth_database_test')
    DB_PORT = Field(env='DB_PORT', default=5432)

    TESTING = Field(env='TESTING', default=True)

    FLASK_HOST = Field(env='FLASK_HOST', default='127.0.0.1')
    FLASK_PORT = Field(env='FLASK_PORT', default=8000)

    REDIS_HOST = Field(env='REDIS_HOST', default='127.0.0.1')
    REDIS_PORT = Field(env='REDIS_PORT', default=6379)
    REDIS_DB = Field(env='REDIS_DB', default=0)

    ACCESS_EXPIRES_IN_HOURS = Field(env='ACCESS_EXPIRES_IN_HOURS', default=1)
    REFRESH_EXPIRES_IN_DAYS = Field(env='REFRESH_EXPIRES_IN_DAYS', default=1)
    SECRET_KEY = Field(env='JWT_SECRET_KEY', default='secret_key')

    JAEGER_HOST = Field(env='JAEGER_HOST', default='127.0.0.1')
    JAEGER_PORT = Field(env='JAEGER_PORT', default=6831)


settings = Settings()
