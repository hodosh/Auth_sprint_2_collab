from datetime import timedelta
from http import HTTPStatus

from apifairy import response, body
from flask import abort, url_for, redirect, request
from flask_jwt_extended import create_access_token, get_jwt, jwt_required

from project.core.config import settings
from project.extensions import jwt_redis_blocklist, log_activity
from project.models.models import User
from project.schemas import token_schema, message_schema, login_schema
from project.services.social_auth import ExternalAuthActions
from project.utils.parsed_user_agent import get_platform
from project.utils.rate_limiter import rate_limit
from . import auth_api_blueprint


@auth_api_blueprint.route('/login', methods=['POST'])
@rate_limit(by_ip=True)
@body(login_schema)
@response(token_schema, HTTPStatus.OK)
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

    log_activity(user_id=user.id, activity='login', platform=get_platform(request.user_agent.string))
    return dict(token=access_token)


@auth_api_blueprint.route('/logout', methods=['DELETE'])
@jwt_required()
@rate_limit(by_email=True, by_ip=True)
@response(message_schema, HTTPStatus.OK)
def logout():
    """Logout endpoint"""
    jwt = get_jwt()
    jti = jwt['jti']
    jwt_redis_blocklist.set(jti, '', ex=timedelta(settings.ACCESS_EXPIRES_IN_HOURS))
    email = jwt['sub']
    user = User.query.filter_by(email=email).first()

    if not user:
        abort(HTTPStatus.NOT_FOUND, f'user with email={email} not found')
    log_activity(user_id=user.id, activity='logout', platform=get_platform(request.user_agent.string))
    return dict(message='Access token revoked')


@auth_api_blueprint.route('/login/<provider>', methods=['GET'])
@rate_limit(by_ip=True)
def login_provider(provider: str):
    """Login with Google+Yandex"""
    return ExternalAuthActions.login_redirect(provider)


@auth_api_blueprint.route('/authorize/<provider>', methods=['GET'])
@rate_limit(by_ip=True)
def authorize(provider: str):
    """Authorize with Google+Yandex"""
    email = ExternalAuthActions.check_email(provider)
    # check user in database
    user = User.query.filter_by(email=email, disabled=False).first()

    if not user:
        reg_url = url_for('users.register')
        return redirect(reg_url, HTTPStatus.FOUND)

    additional_claims = {'role_id': user.role_id}
    access_token = create_access_token(identity=email, additional_claims=additional_claims)

    log_activity(user_id=user.id, activity=f'login with {provider}', platform=get_platform(request.user_agent.string))
    return dict(token=access_token)
