import typing as t
from http import HTTPStatus

import redis
from flask import abort
from flask_jwt_extended import get_jwt

from project import database, jwt, settings
from project.models.models import (
    UserHistory,
    RolePermission,
    Permission,
    User,
)

jwt_redis_blocklist = redis.StrictRedis(
    host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=settings.REDIS_DB, decode_responses=True
)


@jwt.token_in_blocklist_loader
def check_if_token_is_revoked(jwt_header, jwt_payload: dict):
    jti = jwt_payload["jti"]
    token_in_redis = jwt_redis_blocklist.get(jti)
    return token_in_redis is not None


def log_activity(user_id: str, activity: str):
    user_history = UserHistory(user_id=user_id, activity=activity)
    database.session.add(user_history)
    database.session.commit()


def check_access(permission: t.Union[t.Any, t.List[t.Any]]):
    """
    Декоратор для проверки уровня доступа текущего пользователя.
    :param permission: объект пермишена
    """

    def decorator(func):
        def wrapper(*args, **kwargs):
            email = get_jwt()['sub']
            user = User.query.filter_by(email=email).first()
            if not user:
                abort(HTTPStatus.NOT_FOUND, f'user with email={email} not found')
            role_id = user.role_id
            if not role_id:
                abort(HTTPStatus.FORBIDDEN, f'user with id={user.id} has no access for action')

            permission_list = [permission] if not isinstance(permission, list) else permission

            access = any([_check_permission(role_id, p) for p in permission_list])
            if not access:
                abort(HTTPStatus.FORBIDDEN, f'user with id={user.id} has no access for action')

            return func(*args, **kwargs)

        # Renaming the function name:
        wrapper.__name__ = func.__name__
        return wrapper

    return decorator


def _check_permission(role_id, permission) -> bool:
    permission_obj = Permission.query.filter_by(name=permission.value).first()
    if not permission_obj:
        return False

    role_permission = RolePermission.query.filter_by(role_id=role_id, permission_id=permission_obj.id).first()
    if not role_permission:
        return False

    return role_permission.value.lower() == 'true'
