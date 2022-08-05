import time
import uuid
import random

from functools import wraps
from http import HTTPStatus

from flask import abort, request
from flask_jwt_extended import get_jwt

from project import redis

import inflect

WORDY_CAPTCHA_TRIES = 3
WORDY_CAPTCHA_EXPIRATION = 60


def generate_captcha_task():
    num_generator = inflect.engine()
    num1 = random.randint(0, 99)
    num1_srt = num_generator.number_to_words(num1)
    num2 = random.randint(0, 99)
    num2_str = num_generator.number_to_words(num2)

    if random.randint(0, 99) > 50:
        captcha_answer = num1 + num2
        captcha_question = num1_srt + " plus " + num2_str
    else:
        captcha_answer = num1 - num2
        captcha_question = num1_srt + " minus " + num2_str

    return captcha_answer, captcha_question


def save_captcha_task(key, captcha_answer):
    redis.set(key, captcha_answer, expire=WORDY_CAPTCHA_EXPIRATION)


def create_captcha():
    captcha_id = str(uuid.uuid4())
    (captcha_answer, captcha_question) = generate_captcha_task()
    save_captcha_task(captcha_id, captcha_answer)


def validate_catcha(captcha_id, user_answer):
    corrent_answer = redis.get(captcha_id)
    if not corrent_answer:
        return False

    if corrent_answer == user_answer:
        return True
    else:
        return False
