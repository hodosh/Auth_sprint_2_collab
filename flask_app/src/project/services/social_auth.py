from authlib.integrations.flask_client import OAuth

from app import app
from project import settings

oauth = OAuth(app)

# register google auth
google = oauth.register(
    name='google',
    client_id=settings.GOOGLE_CLIENT_ID,
    client_secret=settings.GOOGLE_CLIENT_SECRET,
    access_token_url=settings.GOOGLE_TOKEN_URI,
    access_token_params=None,
    authorize_url=settings.GOOGLE_AUTH_URI,
    authorize_params=None,
    api_base_url=settings.GOOGLE_API_BASE_URL,
    userinfo_endpoint=settings.GOOGLE_USERINFO_URL,  # This is only needed if using openId to fetch user info
    client_kwargs=settings.GOOGLE_SCOPE,
    jwks_uri=settings.GOOGLE_JWKS_URI,
)
# create google client
google_client = oauth.create_client('google')


