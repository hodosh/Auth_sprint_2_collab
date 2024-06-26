from http import HTTPStatus

from apifairy import (
    body,
    response,
)
from flask import abort
from flask_jwt_extended import jwt_required, get_jwt

from project import database
from project.core.permissions import USER_SELF, USER_ALL
from project.extensions import check_access, jwt_redis_blocklist
from project.models.models import (
    User,
    Role,
    RolePermission,
    Permission,
    UserHistory,
)
from project.schemas import (
    new_user_schema,
    user_schema,
    UserSchema,
    update_user_schema,
    new_role_schema,
    user_role_schema,
    pagination_schema,
    paginated_history_schema,
    message_schema,
)
from project.utils.rate_limiter import rate_limit
from project.validators.email import EmailValidator
from project.validators.password import PasswordValidator
from . import users_api_blueprint


@users_api_blueprint.route('/register', methods=['POST'])
@body(new_user_schema)
@response(user_schema, HTTPStatus.CREATED)
def register(kwargs):
    """Create a new user"""
    if not kwargs:
        abort(HTTPStatus.EXPECTATION_FAILED, 'cannot find email, password and password_confirm in data!')
    email = kwargs['email']

    if not EmailValidator.validate(email=email):
        abort(HTTPStatus.EXPECTATION_FAILED, 'email is non valid!')

    password = kwargs['password']
    password_confirm = kwargs['password_confirm']

    if not PasswordValidator.validate(password1=password, password2=password_confirm):
        abort(HTTPStatus.EXPECTATION_FAILED, 'passwords do not match')

    user = User.query.filter_by(email=email).first()
    if user:
        abort(HTTPStatus.EXPECTATION_FAILED, f'user with email={email} exists')

    new_user = User(email=email, password_plaintext=password)

    database.session.add(new_user)
    database.session.commit()

    return new_user


@users_api_blueprint.route('/<user_id>', methods=['POST'])
@jwt_required()
@body(update_user_schema)
@response(user_schema, HTTPStatus.OK)
@check_access(USER_SELF.UPDATE)
def update_user(kwargs, user_id: str):
    """Update user info"""
    if not kwargs:
        abort(HTTPStatus.EXPECTATION_FAILED,
              'cannot find email, old_password, new_password and password_confirm in data!')
    email = kwargs['email']
    old_password = kwargs['old_password']
    new_password = kwargs['new_password']
    new_password_confirm = kwargs['new_password_confirm']

    user = User.query.get(user_id)
    if not user:
        abort(HTTPStatus.NOT_FOUND, f'user with user_id={user_id} not found')

    if not user.is_password_correct(old_password):
        abort(HTTPStatus.EXPECTATION_FAILED, 'old password is incorrect')

    if not new_password:
        abort(HTTPStatus.EXPECTATION_FAILED, 'new password is not specified')

    if new_password != new_password_confirm:
        abort(HTTPStatus.EXPECTATION_FAILED, 'passwords do not match')

    user.email = email
    user.set_password(new_password)

    database.session.commit()

    return user


@users_api_blueprint.route('/<user_id>', methods=['DELETE'])
@jwt_required()
@response(user_schema, HTTPStatus.OK)
@check_access(USER_ALL.DELETE)
def disable_user(user_id: str):
    """Disable user"""
    user = User.query.get(user_id)
    if not user.is_enabled():
        abort(HTTPStatus.EXPECTATION_FAILED, f'user with user_id={user_id} is already disabled')

    user.disable()
    database.session.commit()

    return user


@users_api_blueprint.route('/', methods=['GET'])
@jwt_required()
@response(UserSchema(many=True), HTTPStatus.OK)
@rate_limit(by_email=True, by_ip=True)
@check_access(USER_ALL.READ)
def get_all_users():
    """Disable user"""
    users = User.query.order_by(User.email).all()
    if not users:
        abort(HTTPStatus.NOT_FOUND, 'users not found')

    return users


@users_api_blueprint.route('/<user_id>', methods=['GET'])
@jwt_required()
@response(user_schema, HTTPStatus.OK)
@rate_limit(by_email=True, by_ip=True)
@check_access(USER_SELF.READ)
def get_user(user_id: str):
    """Get user info"""
    user = User.query.get(user_id)
    if not user:
        abort(HTTPStatus.NOT_FOUND, f'user with user_id={user_id} not found')

    return user


@users_api_blueprint.route('/<user_id>/role', methods=['GET'])
@jwt_required()
@response(new_role_schema, HTTPStatus.OK)
@rate_limit(by_email=True, by_ip=True)
@check_access([USER_SELF.READ])
def get_user_role(user_id: str):
    """Get user's role info"""
    user = User.query.get(user_id)
    if not user:
        abort(HTTPStatus.NOT_FOUND, f'user with user_id={user_id} not found')

    jwt = get_jwt()

    role_id = jwt['role_id']
    if not role_id:
        abort(HTTPStatus.NOT_FOUND, f'user with id={user_id} has no any role')

    role_permissions = RolePermission.query.filter_by(role_id=role_id)
    if not role_permissions:
        abort(HTTPStatus.NOT_FOUND, f'role with id={role_id} have no any permissions')

    permissions_list = [Permission.query.get(role_permission.permission_id) for role_permission in role_permissions]
    role = Role.query.get(role_id)

    return dict(name=role.name, permissions=permissions_list)


@users_api_blueprint.route('/<user_id>/role/<role_id>', methods=['PUT'])
@jwt_required()
@response(user_role_schema, HTTPStatus.OK)
@rate_limit(by_email=True, by_ip=True)
@check_access([USER_SELF.UPDATE, USER_ALL.UPDATE])
def set_user_role(user_id: str, role_id: str):
    """Set new role to user"""
    user = User.query.get(user_id)
    if not user:
        abort(HTTPStatus.NOT_FOUND, f'user with id={user_id} not found')

    role = Role.query.get(role_id)
    if not role:
        abort(HTTPStatus.NOT_FOUND, f'role with id={role_id} not found')

    user_role_id = user.role_id
    if user_role_id == role_id:
        abort(HTTPStatus.EXPECTATION_FAILED, f'user with id={user_id} already has role with id={role_id}')

    user.role_id = role_id
    database.session.commit()

    return user


@users_api_blueprint.route('/<user_id>/history', methods=['GET'])
@jwt_required()
@body(pagination_schema)
@response(paginated_history_schema, HTTPStatus.OK)
@rate_limit(by_email=True, by_ip=True)
@check_access([USER_SELF.READ, USER_ALL.READ])
def get_user_session_history(kwargs, user_id: str):
    """Get user's history"""
    page = kwargs['page'] if kwargs else 1
    per_page = kwargs['per_page'] if kwargs else 10

    user_history: UserHistory = UserHistory.query.filter_by(user_id=user_id).paginate(page, per_page, error_out=False)
    if not user_history.items:
        abort(HTTPStatus.NOT_FOUND, f'user with user_id={user_id} has no history yet!')

    return dict(history=user_history.items, page=page, per_page=per_page)


@users_api_blueprint.route('/check_access', methods=['GET'])
@jwt_required()
@rate_limit(by_email=True, by_ip=True)
@response(message_schema, HTTPStatus.OK)
def check_access():
    """validate token"""
    jwt = get_jwt()
    jti = jwt['jti']
    if jwt_redis_blocklist.get(jti):
        abort(HTTPStatus.NOT_FOUND, 'token is revoked')

    email = jwt['sub']
    user = User.query.filter_by(email=email).first()
    if not user:
        abort(HTTPStatus.NOT_FOUND, 'user not found')

    if user.disabled:
        abort(HTTPStatus.FORBIDDEN, 'user disabled')

    role_id = jwt['role_id']
    if not role_id:
        abort(HTTPStatus.NOT_FOUND, 'user has no any access')

    return dict(message='Success')
