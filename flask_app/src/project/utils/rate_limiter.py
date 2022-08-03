import time
from functools import wraps
from http import HTTPStatus

from flask import abort, request
from flask_jwt_extended import get_jwt

from project import redis


def rate_limit(limit: int = 10, interval: int = 60, by_email: bool = False, by_ip: bool = False):
    """
    Rate limiter для запросов от пользователя
    @param limit: лимит подключений за интервал
    @param interval: интервал в секундах
    @param by_email: условие ограничения по почтовому ящику
    @param by_ip: условие ограничения по ip
    """
    def rate_limit_decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if by_email or by_ip:
                prefix = ''
                if by_email:
                    email = get_jwt()['sub']
                    prefix = f'{prefix}{email}:'
                if by_ip:
                    prefix = f'{prefix}{request.remote_addr}:'
                t = int(time.time())
                closest_minute = t - (t % interval)
                key = f'{prefix}{closest_minute}'
                current = redis.get(key)
                if current and int(current) > limit:
                    abort(HTTPStatus.TOO_MANY_REQUESTS, f'Too many requests for {prefix.rstrip(":")}')

                pipe = redis.pipeline()
                pipe.incr(key, 1)
                pipe.expire(key, interval + 1)
                pipe.execute()

            return f(*args, **kwargs)

        return wrapper

    return rate_limit_decorator
