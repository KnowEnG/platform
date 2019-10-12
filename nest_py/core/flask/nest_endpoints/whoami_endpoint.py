import traceback

import flask

from nest_py.core.flask.nest_endpoints.nest_endpoint import NestEndpoint

class WhoamiEndpoint(NestEndpoint):
    """
    simple endpoint that tells the caller what
    the server knows about the caller and the
    request
    """

    def __init__(self, authenticator):
        relative_url = 'whoami'
        super(WhoamiEndpoint, self).__init__(relative_url, authenticator)
        return

    def get_flask_rule(self):
        return 'whoami'

    def get_flask_endpoint(self):
        return 'whoami'

    def handle_request(self, **kwargs):
        #print('whoami.handle_request')
        request = flask.request #this is a global

        jdata = dict()
        jdata['method'] = request.method
        user_jd = None
        try:
            requesting_user = self.authenticator.authenticate_token(request)
            if requesting_user is None:
                user_jd = 'NO_AUTH_TOKEN'
            else:
                user_jd = requesting_user.to_jdata()
        except Exception:
            traceback.print_exc()
        jdata['user'] = user_jd
        jdata['kwargs'] = dict(**kwargs)
        jdata['args'] = dict(request.args)
        jdata['headers'] = dict(request.headers)
        jdata['cookies'] = dict(request.cookies)
        jdata['url'] = request.url
        jdata['form'] = dict(request.form)
        resp = self._make_success_json_response(jdata)
        return resp
