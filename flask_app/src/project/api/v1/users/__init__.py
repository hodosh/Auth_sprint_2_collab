"""
The 'users' blueprint handles the API for managing users.
"""
from flask import Blueprint


users_api_blueprint = Blueprint('users', __name__)

from . import routes
