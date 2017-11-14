import flask
import json
import traceback

class NestEndpoint(object):
    """
    an abstract class over the HTTP methods and an endpoint 
    (relative url)
    """

    def __init__(self, relative_url, authenticator, require_auth=True):
        """
        authenticator (AuthenticationStrategy): provides
        a NestUser based on any incoming request that the
        endpoint can then use to determine what data the user
        is authorized to see (if any).
        require_auth (bool): if True, the endpoint will immediately
            return a 401 error if the request doesn't have a valid
            jwt token associated with a NestUser

        TODO: remove relative_url? is it jsut flask_ep now?
        """
        self.relative_url = relative_url
        self.authenticator = authenticator
        self.require_auth = require_auth
        return

    def _make_error_response(self, msg):
        """
        generic catchall error response
        """
        resp = flask.make_response(msg, 500)
        return resp

    def _make_success_json_response(self, resp_jdata):
        payload = json.dumps(resp_jdata)
        resp = flask.make_response(payload, 200)
        resp.headers['Content-Type'] = 'application/json'
        return resp
 
    def get_flask_rule(self):
        rule = None
        raise Exception("Abstract Class. Not Implemented")
        return rule
    
    def get_flask_endpoint(self):
        """
        note that what flask calls an 'endpoint' is just a unique
        key to be able to look up the 'rule' within the flask
        context. The endpoint can be totally different from
        the rule and therefore the url that it is accessed by.
        """
        flask_ep = None
        raise Exception("Abstract Class. Not Implemented")
        return flask_ep

    def get_relative_url(self):
        return self.relative_url

    def handle_request(self, **kwargs):
        """
        *args will be added by the flask parse rule. so if
        the url_rule ends with "/accounts/<name>/numbers/<int:xyz>",
        then args will be "name, xyz"
        """
        #print('NestEndpoint.handle_request')
        try:
            request = flask.request #this is a global
            requesting_user = self.authenticator.authenticate_token(request)
            if requesting_user is None and self.require_auth:
                resp = flask.make_response('No valid jwt_token in headers', 401)
            else:
                if request.method == 'POST':
                    resp = self.do_POST(request, requesting_user, **kwargs)
                elif request.method == 'GET':
                    resp = self.do_GET(request, requesting_user, **kwargs)
                elif request.method == 'DELETE':
                    resp = self.do_DELETE(request, requesting_user,  **kwargs)
                elif request.method == 'PATCH':
                    resp = self.do_PATCH(request, requesting_user,  **kwargs)
                else:
                    payload = (str(request.method) + 
                        ' not supported at this endpoint')
                    resp = flask.make_response(payload, 405)
        except Exception as e:
            # TODO consider: if it's a werkzeug exception, instead of
            # hardcoding a 500 status, use its get_response() method
            traceback.print_exc()
            msg = "Unhandled Exception: " + str(e)
            resp = flask.make_response(msg, 500)
        #FIXME: currently this may override any competing headers
        #that the request handlers may have added (if they have the same name)
        #need to figure out a consistent way to override those added below
        self.add_cache_control_headers(resp)
        return resp

    def do_GET(self, request, requesting_user, **kwargs):
        payload = "GET not supported at this endpoint"
        resp = flask.make_response(payload, 405)
        return resp

    def do_POST(self, request, requesting_user, **kwargs):
        payload = "POST not supported at this endpoint"
        resp = flask.make_response(payload, 405)
        return resp

    def do_PATCH(self, request, requesting_user, **kwargs):
        payload = "PATCH not supported at this endpoint"
        resp = flask.make_response(payload, 405)
        return resp

    def do_DELETE(self, request, requesting_user, **kwargs):
        payload = "DELETE not supported at this endpoint"
        resp = flask.make_response(payload, 405)
        return resp
  
    def add_cache_control_headers(self, response):
        """
        Adds standard headers:

        Cache-Control: no-store, no-cache, must-revalidate
        Pragma: no-cache
        Expires: 0
        """ 
        try:
            cache_headers = dict()
            cache_headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            cache_headers['Pragma'] = 'no-cache'
            cache_headers['Expires'] = '0'
            response.headers.extend(cache_headers)
        except Exception as e:
            traceback.print_exc()
        return

def log(msg):
    print(msg)
