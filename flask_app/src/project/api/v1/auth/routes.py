from datetime import timedelta
from http import HTTPStatus

from apifairy import response, body
from flask import abort, url_for, session, redirect
from flask_jwt_extended import create_access_token, get_jwt, jwt_required

from project.core.config import settings
from project.extensions import jwt_redis_blocklist, log_activity
from project.models.models import User
from project.schemas import token_schema, message_schema, login_schema
from project.services.social_auth import oauth, google_client
from . import auth_api_blueprint


@auth_api_blueprint.route('/')
def hello_world():
    email = dict(session)['profile']['email']
    return f'Hello, you are logged in as {email}!'


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


@auth_api_blueprint.route('/login/google', methods=['GET'])
def login_google():
    """Login with Google"""
    redirect_uri = url_for('auth.authorize', _external=True)
    res = google_client.authorize_redirect(redirect_uri)

    return res


@auth_api_blueprint.route('/authorize', methods=['GET'])
def authorize():
    token = google_client.authorize_access_token()  # Access token from google (needed to get user info)

    userinfo = oauth.google.userinfo()
    email = userinfo['email']
    user = User.query.filter_by(email=email, disabled=False).first()

    if not user:
        reg_url = url_for('users.register')
        return redirect(reg_url, 302)

    session['profile'] = userinfo
    session.permanent = True  # make the session permanant so it keeps existing after broweser gets closed
    additional_claims = {'role_id': user.role_id}
    access_token = create_access_token(identity=email, additional_claims=additional_claims)
    log_activity(user.id, 'login with Google')

    return dict(token=access_token)
