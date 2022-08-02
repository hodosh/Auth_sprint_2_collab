import time
from functools import wraps
from http import HTTPStatus

from flask import abort
from flask_jwt_extended import get_jwt

from project import redis
from project.models.models import User


def rate_limit(limit=10, interval=60):
    def rate_limit_decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            email = get_jwt()['sub']
            user = User.query.filter_by(email=email).first()
            if not user:
                abort(HTTPStatus.NOT_FOUND, f'User with email={email} not found')

            t = int(time.time())
            closest_minute = t - (t % interval)
            key = f'{user.id}:{closest_minute}'
            current = redis.get(key)
            if current and int(current) > limit:
                abort(HTTPStatus.TOO_MANY_REQUESTS, f'Too many requests for {email}')

            pipe = redis.pipeline()
            pipe.incr(key, 1)
            pipe.expire(key, interval + 1)
            pipe.execute()

            return f(*args, **kwargs)

        return wrapper

    return rate_limit_decorator
