"""This module supports authentication for KnowEnG.
"""
import pymysql
import traceback
from werkzeug.exceptions import UnsupportedMediaType
from nest_py.core.flask.accounts.authentication import NativeAuthenticationStrategy
from nest_py.core.data_types.nest_user import NestUser

import nest_py.core.db.db_ops_utils as db_ops_utils


class HubzeroAuthenticationStrategy(NativeAuthenticationStrategy):
    """Authentication strategy for HUBZero.
    
        Note that this class overrides the authenticate() method to
        sign a user in at the sessions endpoint using a HZ session Id.
        It does NOT override the authenticate_token() method that 
        then validates the jwt token used thereafter.
    """

    def __init__(self, app, users_db_client):
        """Initializes self.

        Args:
            app (Eve): The application object.
        """
        self.users_db_client = users_db_client
        self.app_host = app.config['HUBZERO_APPLICATION_HOST']
        self.db_host = app.config['HUBZERO_DATABASE_HOST']
        self.db_username = app.config['HUBZERO_DATABASE_USERNAME']
        self.db_password = app.config['HUBZERO_DATABASE_PASSWORD']
        self.db_name = app.config['HUBZERO_DATABASE_NAME']
        print('app_host: ' + self.app_host)
        print('db_host: ' + self.db_host)
        print('db_username: ' + self.db_username)
        print('db_password: ' + self.db_password)
        print('db_name: ' + self.db_name)
        if len(self.app_host) == 0:
            raise AttributeError('HUBZERO_APPLICATION_HOST cannot be empty')
        if len(self.db_host) == 0:
            raise AttributeError('HUBZERO_DATABASE_HOST cannot be empty')
        if len(self.db_username) == 0:
            raise AttributeError('HUBZERO_DATABASE_USERNAME cannot be empty')
        if len(self.db_password) == 0:
            raise AttributeError('HUBZERO_DATABASE_PASSWORD cannot be empty')
        if len(self.db_name) == 0:
            raise AttributeError('HUBZERO_DATABASE_NAME cannot be empty')
        if ' ' in self.app_host:
            raise AttributeError(\
                'HUBZERO_APPLICATION_HOST cannot contain spaces')
        if ' ' in self.db_host:
            raise AttributeError(\
                'HUBZERO_DATABASE_HOST cannot contain spaces')
        if ' ' in self.db_username:
            raise AttributeError(\
                'HUBZERO_DATABASE_USERNAME cannot contain spaces')
        if ' ' in self.db_password:
            raise AttributeError(\
                'HUBZERO_DATABASE_PASSWORD cannot contain spaces')
        if ' ' in self.db_name:
            raise AttributeError(\
                'HUBZERO_DATABASE_NAME cannot contain spaces')
        super(HubzeroAuthenticationStrategy, self).__init__(app, users_db_client)

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
            print('authenticate() handling payload: ' + str(payload))
            #has hz_session and it's not empty string 
            if 'hz_session' in payload and (payload['hz_session']): 
                hz_session = payload.get('hz_session', None)
                if hz_session is not None:
                    session_dict = self.fetch_session(hz_session)
                    if session_dict:
                        raw_user = self._session_dict_to_nest_user(session_dict)
                        #this will either retrieve the user from the db if the
                        #hubzero user #has logged in before, or create a new user
                        #in the db with a new nest_id.  #note that if any of the
                        #hubzero fields are different, this will create #a new
                        #local account
                        #TODO: better handling of duplicate usernames
                        registered_user = self._ensure_nest_user(raw_user)
            else:
                print('hubzero auth passing login to superclass')
                #otherwise try the normal username/password login 
                #that the superclass handles
                registered_user = super(
                    HubzeroAuthenticationStrategy, self).authenticate(request)
        else:
            raise UnsupportedMediaType(\
                'expected application/json Content-Type; ' + \
                'got ' + request.headers['Content-Type'])
        return registered_user

    def _session_dict_to_nest_user(self, session_dict):
        nest_id = None
        username = session_dict[u'username']
        given_name = session_dict[u'givenName']
        family_name = session_dict[u'surname']
        origin = 'hubzero'
        external_id = session_dict[u'userid']
        thumbnail_url = self.get_thumbnail_url(\
            session_dict[u'userid'], session_dict[u'picture'])

        nu = NestUser(nest_id, username, given_name, family_name,
            thumb_url=thumbnail_url, origin=origin, 
            external_id=external_id)
        return nu

    def _ensure_nest_user(self, raw_user):
        #look for the user in the db
        uname = raw_user.get_username()
        origin = 'hubzero'
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
            print("Duplicate accounts with username '" + uname + 
                "' detected. Don't know what to do. Denying login")
            registered_tle = None

        if registered_tle is None:
            registered_user = None
        else:
            registered_user = NestUser.from_tablelike_entry(registered_tle)
            db_ops_utils.ensure_default_project(registered_user)
        return registered_user

    def fetch_session(self, session):
        """Given a HUBZero session ID, returns a dictionary user attributes if
        the session is still valid, or None if the session is not valid.

        TODO: Can we replace all of this? Would be much better if HUBZero could
        issue tokens of its own or provide an API. This is all based on
        undocumented HZ implementation details that are likely subject to
        change without notice.

        Args:
            session (str): HUBZero session ID.

        Returns:
            dict: A dictionary of user attributes if the session is valid, or
            None if the session is not valid.
        """
        # HUBZero tables of interest:
        # jos_session:
        #   session_id
        #   userid
        #   username
        #   ip
        # jos_xprofiles:
        #   uidNumber (matches jos_session.userid)
        #   username (matches jos_session.username)
        #   givenName, surname
        #   email
        #   homeDirectory
        #   orgtype (look for 'researcher')
        #   picture (either blank or 'profile.png' in cases I saw, even after
        #     uploading differently named file)
        # jos_users_log_auth

        # note: if user is recognized but not yet authenticated, jos_session row
        # will not have the userid, which is the behavior we want
        # note: if user logs out, jos_session row will not have the userid,
        # which is also the behavior we want

        return_val = None
        # TODO bother with connection pooling?
        try:
            con = pymysql.connect(\
                self.db_host, self.db_username, self.db_password, self.db_name)
            with con:
                cur = con.cursor(pymysql.cursors.DictCursor)
                cur.execute("SELECT s.userid, s.username, s.ip, " + \
                    "p.givenName, p.surname, p.email, p.homeDirectory, " + \
                    "'researcher' AS orgtype, '' AS picture " + \
                    "FROM jos_session s INNER JOIN jos_users p " + \
                    "ON s.userid = p.id WHERE session_id = %s", \
                    (session))
                rows = cur.fetchall()
                print('HUBZERO DB returned: ' + str(rows))
                if len(rows) == 1:
                    return_val = rows[0]
        except Exception as e:
            traceback.print_exc()
            
        return return_val

    def get_thumbnail_url(self, userid, picture):
        """Given jos_session.userid and jos_xprofiles.picture from HUBZero,
        returns the URL for the user's profile image thumbnail.

        TODO: Can we replace all of this? Would be much better if HUBZero could
        issue tokens of its own or provide an API. This is all based on
        undocumented HZ implementation details that are likely subject to
        change without notice.

        Args:
            userid (str): HUBZero jos_session.userid.
            picture (str): HUBZero jos_xprofiles.picture.

        Returns:
            str: The URL for the user's profile image thumbnail, or '' if the
            user has no profile image.
        """
        return_val = ''
        if picture:
            return_val = 'http://' + self.app_host + '/members/' + \
                str(userid) + '/Image:thumb.png'
        return return_val

