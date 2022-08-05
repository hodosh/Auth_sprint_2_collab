"""
The 'roles' blueprint handles the API for managing roles and their permissions.
"""
from flask import Blueprint

role_api_blueprint = Blueprint('roles', __name__, template_folder='templates')

from . import routes
