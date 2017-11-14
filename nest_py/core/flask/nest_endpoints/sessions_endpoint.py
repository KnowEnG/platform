import json
import flask
import traceback

from flask import Response

from nest_py.core.flask.nest_endpoints.nest_endpoint import NestEndpoint

class SessionsEndpoint(NestEndpoint):

    def __init__(self, authenticator):
    
        self.flask_ep = 'sessions'
        self.flask_rule = 'sessions'
        #this is where the user logs in, this is the flag that says they
        #don't have to be already logged in
        require_auth = False
        super(SessionsEndpoint, self).__init__(self.flask_ep, 
            authenticator, require_auth=require_auth)
        return 

    def get_flask_rule(self):
        return self.flask_rule

    def get_flask_endpoint(self):
        return self.flask_ep

    def do_POST(self, request, requesting_user):
        """
        called when someone POSTs credentials to the 'sessions' endpoint
        """
        token = None
        try:
            user = self.authenticator.authenticate(request)
            if user is not None:
                token = self.authenticator.create_token_for_user(user)
        except Exception:
            traceback.print_exc()
            token = None
        if token is not None:
            resp_json = '{"access_token": "' + token + '"}'
            response = Response(
                response=resp_json, 
                status=200, 
                mimetype="application/json")
        else:
            response = Response(response='{}', \
                status=403, mimetype="application/json")
        return response
