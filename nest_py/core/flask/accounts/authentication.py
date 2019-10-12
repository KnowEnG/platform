"""This module defines strategies for authenticating users from HTTP requests.

Here's the idea:

1. Application clients (UI or headless) authenticate via the `sessions/`
   endpoint from the `public` blueprint. We currently support two kinds of
   authentication:

   - username and password hash matched against our own database: see
   NativeAuthenticationStrategy below.

   - trusted third-party authentication via CILogon: see
   CILogonAuthenticationStrategy.

   A successful authentication request will be answered with a JWT token.

2. Authorization relies on these JWT tokens.

   - NestEndpoints can enforce authorization rules. Adding
     `'authentication': JWTAuth` to a domain causes Eve to reject requests that
     don't contain a valid token in the header. Futher adding an `auth_field`
     to the domain automatically associates each record with its creator's user
     ID and allows only the creator to access the record in subsequent endpoint
     calls. Other authorization rules are possible; see the Eve documentation
     on authorization.

   - The Angular2 application will refuse to load certain routes unless the user
     has a valid token.
"""

import traceback
from werkzeug.exceptions import UnsupportedMediaType
from nest_py.core.data_types.nest_user import NestUser
from nest_py.core.flask.accounts.token import TokenAgent
import nest_py.core.flask.accounts.password_hash as password_hash
import nest_py.core.db.core_db as core_db

class AuthenticationStrategy(object):
    """Base class for authentication strategies."""

    def __init__(self, app):
        """Initializes self.

        Args:
            app (Eve): The application object.
        """
        self.app = app

    def authenticate(self, request):
        """Attempts to authenticate a user from an HTTP request.

        Args:
            request (flask.request): The request object.

        Returns:
            NestUser: Valid, populated object representing the user if
            authentication succeeded, else None.
        """
        raise NotImplementedError

class NativeAuthenticationStrategy(AuthenticationStrategy):
    """Authentication strategy for users defined in the local db."""

    def __init__(self, app, users_db_client):
        """Initializes self.

        Args:
            app (Eve): The application object.
            self.token_agent = token_agent
        """
        self.users_db_client = users_db_client
        self.token_agent = None
        self._init_token_agent(app.config)

        super(NativeAuthenticationStrategy, self).__init__(app)
        return

    def _init_token_agent(self, config):
        jwt_secret = config['JWT_SECRET']
        jwt_issuer = config['JWT_ISSUER']
        jwt_audiences = config['JWT_AUDIENCES']
        default_lifespan = config['JWT_LIFESPAN']
        self.token_agent = TokenAgent(jwt_secret, jwt_issuer, \
            jwt_audiences, default_lifespan=default_lifespan)
        return

    def authenticate(self, request):
        """Attempts to authenticate a user from an HTTP request by
        inspecting the username and password in the request's data

        Args:
            request (flask.request): The request object.

        Returns:
            NestUser: Valid, populated object representing the user if
            authentication succeeded, else None.
        TODO: maybe this should all move into the sessions endpoint
            so we can provide better error responses based on where
            a login fails (unknown username, bad password, etc)
        """
        content_type = request.headers['Content-Type']
        if 'application/json' in content_type:
            payload = request.get_json()
            username = payload.get('username', '')
            password = payload.get('password', '')
            sys_user = core_db.get_system_user()
            self.users_db_client.set_requesting_user(sys_user)
            user_tles = self.users_db_client.simple_filter_query(
                {'username':username})
            if len(user_tles) == 0:
                print('no user record for user: ' + str(username))
                nest_user = None
            elif len(user_tles) > 1:
                print('duplicate username in db ??? for: ' + str(username))
                nest_user = None
            else:
                user_tle = user_tles[0]
                pw_hash = user_tle.get_value('passlib_hash')
                if password_hash.verify_password(password, pw_hash):
                    nest_user = NestUser.from_tablelike_entry(user_tle)
                else:
                    print('bad password')
                    nest_user = None
        else:
            raise UnsupportedMediaType(\
                'expected application/json Content-Type; ' + \
                'got ' + request.headers['Content-Type'])
        return nest_user

    def authenticate_token(self, request):
        """
        inspects the token in the header of a request and decodes it
        into a valid NestUser, or None if it's invalid, expired, or doesn't exist
        """
        print('request headers: ' + str(request.headers))
        try:
            if 'Authorization' in request.headers:
                auth_field = request.headers['Authorization']
                #should start with 'Bearer '. Not sure why.
                if "Bearer" not in auth_field:
                    print('token was not a Bearer token')
                    nest_user = None
                    return nest_user
                skip_len = len('Bearer ')
                tkn = auth_field[skip_len:]
                tkn_payload = self.token_agent.decode(tkn)
                print('token payload: ' + str(tkn_payload.data))
                if tkn_payload is None:
                    print('token was not decoded into a user')
                    nest_user = None
                else:
                    nest_user = tkn_payload.to_nest_user()
                    print('token was for: ' + str(nest_user))
                    if tkn_payload.is_expired():
                        print('token is expired')
                        nest_user = None
                    else:
                        #the NestUser we have only contains info the token could hold,
                        #we also need the full db entry to use for security_policy's
                        user_tle = self.users_db_client.read_entry(nest_user.get_nest_id())
                        nest_user = NestUser.from_tablelike_entry(user_tle)
                        print('user from db: ' + str(nest_user))
            else:
                print('no auth header found')
                nest_user = None
        except Exception:
            traceback.print_exc()
            raise Exception("Unrecoverable failure decoding token")
        return nest_user

    def create_token_for_user(self, nest_user):
        tkn = self.token_agent.create_for_user(nest_user)
        return tkn

def log(msg):
    print(msg)
