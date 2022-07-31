from datetime import timedelta
from http import HTTPStatus
from urllib.parse import urlencode

import requests
from apifairy import response, body
from flask import abort, url_for, session, redirect, request
from flask_jwt_extended import create_access_token, get_jwt, jwt_required
from requests import post

from project.core.config import settings
from project.extensions import jwt_redis_blocklist, log_activity
from project.models.models import User
from project.schemas import token_schema, message_schema, login_schema
from project.services.social_auth import oauth, google_client
from . import auth_api_blueprint


@auth_api_blueprint.route('/login', methods=['POST'])
@body(login_schema)
@response(token_schema)
def login(kwargs):
    """Login endpoint"""
    if not kwargs:
        abort(HTTPStatus.EXPECTATION_FAILED, 'cannot find email and password in data!')

    email = kwargs['email']
    password = kwargs['password']
    user = User.query.filter_by(email=email, disabled=False).first()

    if not user:
        abort(HTTPStatus.NOT_FOUND, f'user with email={email} not found')

    if not user.is_password_correct(password):
        abort(HTTPStatus.EXPECTATION_FAILED, 'password is incorrect')
    additional_claims = {'role_id': user.role_id}
    access_token = create_access_token(identity=email, additional_claims=additional_claims)
    log_activity(user.id, 'login')
    return dict(token=access_token)


@auth_api_blueprint.route('/logout', methods=['DELETE'])
@jwt_required()
@response(message_schema)
def logout():
    """Logout endpoint"""
    jwt = get_jwt()
    jti = jwt['jti']
    jwt_redis_blocklist.set(jti, '', ex=timedelta(settings.ACCESS_EXPIRES_IN_HOURS))
    email = jwt['sub']
    user = User.query.filter_by(email=email).first()

    if not user:
        abort(HTTPStatus.NOT_FOUND, f'user with email={email} not found')
    log_activity(user.id, 'login')
    return dict(message='Access token revoked')


# GOOGLE AUTH

@auth_api_blueprint.route('/login/google', methods=['GET'])
def login_google():
    """Login with Google"""
    redirect_uri = url_for('auth.authorize_google', _external=True)
    res = google_client.authorize_redirect(redirect_uri)

    return res


@auth_api_blueprint.route('/authorize/google', methods=['GET'])
def authorize_google():
    """Authorize with Google"""
    token = google_client.authorize_access_token()  # Access token from google (needed to get user info)

    userinfo = oauth.google.userinfo()
    email = userinfo['email']
    user = User.query.filter_by(email=email, disabled=False).first()

    if not user:
        reg_url = url_for('users.register')
        return redirect(reg_url, 302)

    session['profile'] = userinfo
    session.permanent = True  # make the session permanant so it keeps existing after browser gets closed
    additional_claims = {'role_id': user.role_id}
    access_token = create_access_token(identity=email, additional_claims=additional_claims)
    log_activity(user.id, 'login with Google')

    return dict(token=access_token)


# YANDEX AUTH

@auth_api_blueprint.route('/login/yandex', methods=['GET'])
def login_yandex():
    """Login with Yandex"""
    return redirect(settings.YANDEX_BASE_URL + f'authorize?response_type=code&client_id={settings.YANDEX_CLIENT_ID}')


@auth_api_blueprint.route('/authorize/yandex', methods=['GET'])
def authorize_yandex():
    """Authorize with Yandex"""
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
    user_info_response = requests.get(
        url=settings.YANDEX_LOGIN_INFO_URL,
        params={
            "format": "json",
            "with_openid_identity": 1,
            "oauth_token": access_token,
        },
    ).json()
    email = user_info_response['default_email']

    user = User.query.filter_by(email=email, disabled=False).first()
    if not user:
        reg_url = url_for('users.register')
        return redirect(reg_url, 302)

    session['profile'] = user_info_response
    session.permanent = True  # make the session permanant so it keeps existing after browser gets closed
    additional_claims = {'role_id': user.role_id}
    access_token = create_access_token(identity=email, additional_claims=additional_claims)
    log_activity(user.id, 'login with Yandex')

    return dict(token=access_token)
