import os
from datetime import datetime, timezone, timedelta

from apifairy import APIFairy
from flask import Flask, json
from flask_httpauth import HTTPBasicAuth, HTTPTokenAuth
from flask_jwt_extended import (
    JWTManager,
    get_jwt,
    create_access_token,
    get_jwt_identity,
    set_access_cookies,
)
from flask_marshmallow import Marshmallow
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from werkzeug.exceptions import HTTPException

from project.core import config
# Create the instances of the Flask extensions in the global scope,
# but without any arguments passed in. These instances are not
# attached to the Flask application at this point.
from project.core.config import settings

# -------------
# Configuration
# -------------

apifairy = APIFairy()
ma = Marshmallow()
database = SQLAlchemy()
migrate = Migrate()
basic_auth = HTTPBasicAuth()
token_auth = HTTPTokenAuth()
jwt = JWTManager()


# ------------


def get_api_url():
    return f"http://{settings.FLASK_HOST}:{settings.FLASK_PORT}/v1"


# ----------------------------
# Application Factory Function
# ----------------------------

def create_app():
    # Create the Flask application
    app = Flask(__name__)

    app.secret_key = settings.SECRET_KEY or os.urandom(24)
    # Configure the API documentation
    app.config['APIFAIRY_TITLE'] = settings.PROJECT_NAME
    app.config['APIFAIRY_VERSION'] = '0.1'
    app.config['APIFAIRY_UI'] = 'swagger_ui'

    # Configure the PG DB
    app.config['SQLALCHEMY_DATABASE_URI'] = f"postgresql://{settings.DB_USER}:{settings.DB_PASS}@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"  # noqa E501
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    initialize_extensions(app)
    register_blueprints(app)
    register_error_handlers(app)
    register_cli_command(app)
    # configure_tracer(app)

    return app


# ----------------
# Helper Functions
# ----------------

def initialize_extensions(app):
    # Since the application instance is now created, pass it to each Flask
    # extension instance to bind it to the Flask application instance (app)
    apifairy.init_app(app)
    ma.init_app(app)
    database.init_app(app)

    app.config["JWT_SECRET_KEY"] = settings.SECRET_KEY  # Change this!
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(settings.ACCESS_EXPIRES_IN_HOURS)
    app.config["JWT_REFRESH_TOKEN_EXPIRES"] = timedelta(settings.REFRESH_EXPIRES_IN_DAYS)
    jwt.init_app(app=app)

    @app.after_request
    def refresh_expiring_jwts(response):
        try:
            exp_timestamp = get_jwt()["exp"]
            now = datetime.now(timezone.utc)
            target_timestamp = datetime.timestamp(now + timedelta(minutes=30))
            if target_timestamp > exp_timestamp:
                access_token = create_access_token(identity=get_jwt_identity())
                set_access_cookies(response, access_token)
            return response
        except (RuntimeError, KeyError):
            return response

    import project.models
    migrate.init_app(app, database)

    # add tracer


def register_blueprints(app):
    # Import the blueprints
    from project.api.v1.role import role_api_blueprint
    from project.api.v1.users import users_api_blueprint
    from project.api.v1.auth import auth_api_blueprint

    # Since the application instance is now created, register each Blueprint
    # with the Flask application instance (app)
    app.register_blueprint(auth_api_blueprint, url_prefix='/api/v1/auth')
    app.register_blueprint(users_api_blueprint, url_prefix='/api/v1/users')
    app.register_blueprint(role_api_blueprint, url_prefix='/api/v1/roles')


def register_error_handlers(app):
    @app.errorhandler(HTTPException)
    def handle_http_exception(e):
        """Return JSON instead of HTML for HTTP errors."""
        # Start with the correct headers and status code from the error
        response = e.get_response()
        # Replace the body with JSON
        response.data = json.dumps({
            'code': e.code,
            'name': e.name,
            'description': e.description,
        })
        response.content_type = 'application/json'
        return response


def register_cli_command(app):
    from project.cli.superuser import user_cli
    from project.cli.default_roles import roles_cli

    app.cli.add_command(user_cli)
    app.cli.add_command(roles_cli)


def configure_tracer(app):
    from flask import request
    from opentelemetry import trace
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
    from opentelemetry.exporter.jaeger.thrift import JaegerExporter

    @app.before_request
    def before_request():
        request_id = request.headers.get('X-Request-Id')
        if not request_id:
            raise RuntimeError('request id is required')

    trace.set_tracer_provider(TracerProvider())
    trace.get_tracer_provider().add_span_processor(
        BatchSpanProcessor(
            JaegerExporter(
                agent_host_name=settings.JAEGER_HOST,
                agent_port=settings.JAEGER_PORT,
            )
        )
    )
    # Чтобы видеть трейсы в консоли
    trace.get_tracer_provider().add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))
    FlaskInstrumentor().instrument_app(app)


# def auth_social_networks(app):
    # from authlib.integrations.flask_client import OAuth
    # oauth = OAuth(app)
    # oauth.register(
    #     name='google',
    #     server_metadata_url=settings.GOOGLE_DISCOVERY_URL,
    #     client_kwargs={
    #         'scope': 'openid email profile'
    #     }
    # )
