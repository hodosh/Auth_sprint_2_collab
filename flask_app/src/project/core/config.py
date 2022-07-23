import os
from datetime import timedelta

from pydantic import BaseSettings


class Settings(BaseSettings):
    # Название проекта. Используется в Swagger-документации
    PROJECT_NAME = 'auth_service'

    # Корень проекта
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    # Database path
    DB_USER = os.getenv('DB_USER', 'app')
    DB_PASS = os.getenv('DB_PASS', '123qwe')
    DB_HOST = os.getenv('DB_HOST', '127.0.0.1')

    DB_NAME = os.getenv('DB_NAME', 'auth_database')
    DB_TEST_NAME = os.getenv('DB_TEST_NAME', 'auth_database_test')
    DB_PORT = os.getenv('DB_PORT', 5432)

    TESTING = os.getenv('TESTING', True)

    FLASK_HOST = os.getenv('FLASK_HOST', '127.0.0.1')
    FLASK_PORT = os.getenv('FLASK_PORT', 8000)

    REDIS_HOST = os.getenv('REDIS_HOST', '127.0.0.1')
    REDIS_PORT = os.getenv('REDIS_PORT', 6379)
    REDIS_DB = os.getenv('REDIS_DB', 0)

    SQLALCHEMY_DATABASE_URI = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}/{DB_NAME}"

    ACCESS_EXPIRES = timedelta(hours=int(os.getenv('ACCESS_EXPIRES_IN_HOURS', 1)))
    REFRESH_EXPIRES = timedelta(days=int(os.getenv('REFRESH_EXPIRES_IN_DAYS', 1)))
    SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'secret_key')


settings = Settings()
