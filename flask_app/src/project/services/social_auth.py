import json
from abc import ABC, abstractmethod
from http import HTTPStatus
from urllib.parse import urlencode

import requests
from flask import (
    url_for,
    request,
    redirect,
    abort,
)
from oauthlib.oauth2 import WebApplicationClient
from requests import post

from project import settings

client = WebApplicationClient(settings.GOOGLE_CLIENT_ID)


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

    @classmethod
    def get_google_provider_cfg(cls):
        return requests.get(settings.GOOGLE_DISCOVERY_URL).json()

    @classmethod
    def login_redirect(cls):
        # вычитываем, по какому URL нужно логиниться в Google
        google_provider_cfg = cls.get_google_provider_cfg()
        authorization_endpoint = google_provider_cfg['authorization_endpoint']

        # собираем запрос в для логина в Google вместе со скопом
        request_uri = client.prepare_request_uri(
            authorization_endpoint,
            redirect_uri=f'{settings.FLASK_HOST}:{settings.FLASK_PORT}{url_for("auth.authorize", provider="google")}',
            scope=settings.GOOGLE_SCOPE,
        )

        return redirect(request_uri)

    @classmethod
    def check_response_and_get_email(cls) -> str:
        code = request.args.get('code')
        google_provider_cfg = cls.get_google_provider_cfg()
        token_endpoint = google_provider_cfg["token_endpoint"]
        token_url, headers, body = client.prepare_token_request(
            token_endpoint,
            authorization_response=request.url,
            redirect_url=request.base_url,
            code=code
        )
        token_response = requests.post(
            token_url,
            headers=headers,
            data=body,
            auth=(settings.GOOGLE_CLIENT_ID, settings.GOOGLE_CLIENT_SECRET),
        )
        # парсим токен
        client.parse_request_body_response(json.dumps(token_response.json()))
        # читаем юзеринфо
        userinfo_endpoint = google_provider_cfg["userinfo_endpoint"]
        uri, headers, body = client.add_token(userinfo_endpoint)
        userinfo_response = requests.get(uri, headers=headers, data=body)
        # забираем только почту
        return userinfo_response.json()['email']


class YandexProvider(BaseProvider):

    @classmethod
    def login_redirect(cls):
        return redirect(
            settings.YANDEX_BASE_URL + f'authorize?response_type=code&client_id={settings.YANDEX_CLIENT_ID}')

    @classmethod
    def check_response_and_get_email(cls) -> str:
        data = {
            'grant_type': 'authorization_code',
            'code': request.args.get('code'),
            'client_id': settings.YANDEX_CLIENT_ID,
            'client_secret': settings.YANDEX_CLIENT_SECRET,
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

    @classmethod
    def get_provider_instance(cls, provider_name: str) -> BaseProvider:
        """
        Метод для получения класса конкретного провайдера по его имени
        """
        if provider_name.lower() == 'google':
            return GoogleProvider

        elif provider_name.lower() == 'yandex':
            return YandexProvider

        else:
            abort(HTTPStatus.NOT_FOUND, f'wrong type of provider: {provider_name}')

    @classmethod
    def login_redirect(cls, provider_name: str):
        """
        Метод перенаправляет логин на внешний сервис по имени провайдера
        """
        provider = ExternalAuthActions.get_provider_instance(provider_name)
        return provider.login_redirect()

    @classmethod
    def check_email(cls, provider_name: str):
        """
        Метод проверяет ответ (его правомерность) и возвращает почтовый ящик
        """
        provider = ExternalAuthActions.get_provider_instance(provider_name)
        return provider.check_response_and_get_email()
