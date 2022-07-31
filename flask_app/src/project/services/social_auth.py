from abc import ABC, abstractmethod
from http import HTTPStatus
from urllib.parse import urlencode

import requests
from authlib.integrations.flask_client import OAuth
from flask import url_for, request, redirect, abort
from requests import post

from app import app
from project import settings

oauth = OAuth(app)

# register google auth
google = oauth.register(
    name='google',
    client_id=settings.GOOGLE_CLIENT_ID,
    client_secret=settings.GOOGLE_CLIENT_SECRET,
    access_token_url=settings.GOOGLE_TOKEN_URI,
    access_token_params=None,
    authorize_url=settings.GOOGLE_AUTH_URI,
    authorize_params=None,
    api_base_url=settings.GOOGLE_API_BASE_URL,
    userinfo_endpoint=settings.GOOGLE_USERINFO_URL,  # This is only needed if using openId to fetch user info
    client_kwargs=settings.GOOGLE_SCOPE,
    jwks_uri=settings.GOOGLE_JWKS_URI,
)
# create google client
google_client = oauth.create_client('google')


class BaseProvider(ABC):
    def __init__(self, provider_name: str):
        self.provider_name = provider_name

    @abstractmethod
    def login_redirect(self):
        pass

    @abstractmethod
    def check_response_and_get_email(self):
        pass


class GoogleProvider(BaseProvider):
    def __init__(self, provider_name: str):
        super().__init__(provider_name)
        self.provider_name = provider_name

    @staticmethod
    def login_redirect():
        return redirect(
            settings.YANDEX_BASE_URL + f'authorize?response_type=code&client_id={settings.YANDEX_CLIENT_ID}')

    @staticmethod
    def check_response_and_get_email() -> str:
        token = google_client.authorize_access_token()  # Access token from google (needed to get user info)
        userinfo = oauth.google.userinfo()
        return userinfo['email']


class YandexProvider(BaseProvider):
    def __init__(self, provider_name: str):
        super().__init__(provider_name)
        self.provider_name = provider_name

    @staticmethod
    def login_redirect():
        redirect_uri = url_for('auth.authorize_google', _external=True)
        return google_client.authorize_redirect(redirect_uri)

    @staticmethod
    def check_response_and_get_email() -> str:
        data = {
            'grant_type': 'authorization_code',
            'code': request.args.get('code'),
            'client_id': settings.YANDEX_CLIENT_ID,
            'client_secret': settings.GOOGLE_CLIENT_SECRET,
        }
        data = urlencode(data)
        resp = post(settings.YANDEX_BASE_URL + 'token', data).json()
        # Токен необходимо сохранить для использования в запросах к API
        access_token: str = resp.get('access_token')
        userinfo = requests.get(
            url=settings.YANDEX_LOGIN_INFO_URL,
            params={
                "format": "json",
                "with_openid_identity": 1,
                "oauth_token": access_token,
            },
        ).json()
        return userinfo['default_email']


class ExternalAuthActions:

    @staticmethod
    def get_provider_instance(provider_name: str) -> BaseProvider:
        """
        Метод для получения класса конкретного провайдера по его имени
        """
        if provider_name.lower() == 'google':
            return GoogleProvider

        elif provider_name.lower() == 'yandex':
            return YandexProvider

        else:
            abort(HTTPStatus.NOT_FOUND, f'wrong type of provider: {provider_name}')

    @staticmethod
    def login_redirect(provider_name: str):
        """
        Метод перенаправляет логин на внешний сервис по имени провайдера
        """
        provider = ExternalAuthActions.get_provider_instance(provider_name)
        return provider.login_redirect()

    @staticmethod
    def check_email(provider_name: str):
        """
        Метод проверяет ответ (его правомерность) и возвращает почтовый ящик
        """
        provider = ExternalAuthActions.get_provider_instance(provider_name)
        return provider.check_response_and_get_email()
