"""This module supports authentication for KnowEnG.
"""
import traceback
import urllib

import requests
from werkzeug.exceptions import UnsupportedMediaType
from nest_py.core.flask.accounts.authentication import NativeAuthenticationStrategy
from nest_py.core.data_types.nest_user import NestUser

import nest_py.core.db.db_ops_utils as db_ops_utils


class CILogonAuthenticationStrategy(NativeAuthenticationStrategy):
    """Authentication strategy for CILogon.

        Note that this class overrides the authenticate() method to
        sign a user in at the sessions endpoint using a CILogon authorization
        code.
        It does NOT override the authenticate_token() method that
        then validates the jwt token used thereafter.
        Although CILogon does provide us with JWTs, they can't be decoded
        with jwt.decode using the CILogon secret. I (Matt) didn't pursue it
        beyond installing cryptography==2.3, at which point there were still
        issues; perhaps we need cryptographic keys in addition to the token. In
        any case, issuing our own JWTs regardless of which third-party
        authentication services we support could help us keep things simple.

        This roughtly follows the example at https://www.cilogon.org/oidc.
        See nest_py.knoweng.knoweng_config for the CILOGON* parameters and a
        few comments on how to obtain their values.

    """

    def __init__(self, app, users_db_client):
        """Initializes self.

        Args:
            app (Eve): The application object.
            users_db_client (nest_py.core.db.crud_db_client.CrudDbClient): A
                CrudDbClient for the nest_users table.

        """
        self.users_db_client = users_db_client
        self.client_id = app.config['CILOGON_CLIENT_ID']
        self.client_secret = app.config['CILOGON_CLIENT_SECRET']
        self.redirect_uri = app.config['CILOGON_REDIRECT_URI']
        if not self.client_id:
            raise AttributeError('CILOGON_CLIENT_ID cannot be empty')
        if not self.client_secret:
            raise AttributeError('CILOGON_CLIENT_SECRET cannot be empty')
        if not self.redirect_uri:
            raise AttributeError('CILOGON_REDIRECT_URI cannot be empty')
        if ' ' in self.client_id:
            raise AttributeError(\
                'CILOGON_CLIENT_ID cannot contain spaces')
        if ' ' in self.client_secret:
            raise AttributeError(\
                'CILOGON_CLIENT_SECRET cannot contain spaces')
        if ' ' in self.redirect_uri:
            raise AttributeError(\
                'CILOGON_REDIRECT_URI cannot contain spaces')
        super(CILogonAuthenticationStrategy, self).__init__(\
            app, users_db_client)

    def authenticate(self, request):
        """Attempts to authenticate a user from an HTTP request.

        Args:
            request (flask.request): The request object.

        Returns:
            NestUser: Valid, populated object representing the user if
            authentication succeeded, else None.

        """
        registered_user = None
        content_type = request.headers['Content-Type']
        if 'application/json' in content_type:
            payload = request.get_json()
            # has authCode and it's not empty string
            if 'authCode' in payload and payload['authCode']:
                try:
                    auth_code = urllib.unquote_plus(str(payload['authCode']))
                    access_token = self._get_access_token(auth_code)
                    user_info = self._get_user_info(access_token)
                    raw_user = self._user_info_to_nest_user(user_info)
                    # this will either retrieve the user from the db if the
                    # CILogon user has logged in before, or create a new
                    # user in the db with a new nest_id.
                    # TODO: better handling of duplicate usernames
                    registered_user = self._ensure_nest_user(raw_user)
                except Exception as e:
                    print "Authentication attempt raised exception"
                    traceback.print_exc()
            else:
                print('CILogon auth passing login to superclass')
                #otherwise try the normal username/password login
                #that the superclass handles
                registered_user = super(
                    CILogonAuthenticationStrategy, self).authenticate(request)
        else:
            raise UnsupportedMediaType(\
                'expected application/json Content-Type; ' + \
                'got ' + request.headers['Content-Type'])
        return registered_user

    def _get_access_token(self, auth_code):
        """Given a CILogon authentication code, returns the CILogon access
        token.

        Args:
            auth_code (str): CILogon authentication code.

        Returns:
            str: The access token.

        """
        data = {
            'grant_type': 'authorization_code',
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'code': auth_code,
            'redirect_uri': self.redirect_uri
        }
        resp = requests.post('https://cilogon.org/oauth2/token', data=data)
        json = resp.json()
        # json should include keys access_token, id_token, and token_type
        # id_token is the JWT from CILogon, which we could attempt to use;
        # see comments above
        return json['access_token']

    def _get_user_info(self, access_token):
        """Given a CILogon access token, returns a dictionary user attributes.

        Args:
            access_token (str): CILogon access token for this user.

        Returns:
            dict: A dictionary of user attributes. Assuming the client handed
                off the user to CILogon with scopes `openid` (required),
                `profile`, and `email`, we expect the dictionary to look
                something like this:
                {
                    "family_name":"Smith",
                    "sub":"http://cilogon.org/serverA/users/1234",
                    "iss":"https://cilogon.org",
                    "given_name":"John",
                    "email":"jsmith@illinois.edu",
                    "aud": CILOGON_CLIENT_ID
                }

        """
        data = {
            'access_token': access_token
        }
        resp = requests.post('https://cilogon.org/oauth2/userinfo', data=data)
        json = resp.json()
        return json

    def _user_info_to_nest_user(self, user_info):
        """Given the user info returned by `_get_user_info`, returns a NestUser
        instance.

        Args:
            user_info (dict): CILogon user info.

        Returns:
            NestUser: A NestUser object representing the user.

        """
        nest_id = None
        # TODO emails aren't guaranteed to be unique--only the 'sub' field is
        # we should decide our policy for uniqueness of usernames, especially
        # for external users who might never see our own username/password-based
        # login screen
        username = user_info[u'email']
        given_name = user_info[u'given_name']
        family_name = user_info[u'family_name']
        origin = user_info[u'iss']
        external_id = user_info[u'sub']

        nu = NestUser(nest_id, username, given_name, family_name, \
            origin=origin, external_id=external_id)
        return nu

    def _ensure_nest_user(self, raw_user):
        #look for the user in the db
        uname = raw_user.get_username()
        origin = raw_user.get_origin()
        fltr = {'username': uname, 'origin':origin}
        existings = self.users_db_client.simple_filter_query(fltr)
        if len(existings) == 0:
            #user hasn't accessed Nest before, create new NestUser
            raw_tle = raw_user.to_tablelike_entry()
            registered_tle = self.users_db_client.create_entry(raw_tle)
        elif len(existings) == 1:
            #found a valid record of this user in the DB
            registered_tle = existings[0]
            #TODO: add verifications of other name fields?
            #Would we really care if they are different?
        else:
            print("Duplicate accounts with username '" + uname + \
                "' detected. Don't know what to do. Denying login")
            registered_tle = None

        if registered_tle is None:
            registered_user = None
        else:
            registered_user = NestUser.from_tablelike_entry(registered_tle)
            db_ops_utils.ensure_default_project(registered_user)
        return registered_user
