from nest_py.core.flask.nest_endpoints.nest_endpoint import NestEndpoint
import flask


class SimplestEndpoint(NestEndpoint):

    def __init__(self, authenticator):
        relative_url = 'simplest_endpoint'
        super(SimplestEndpoint, self).__init__(relative_url, authenticator)
        return

    def get_flask_endpoint(self):
        return 'simplest_endpoint'

    def get_flask_rule(self):
        return 'simplest_endpoint'

    def do_GET(self, request):
        print('simplestEndpoint.do_GET')
        resp = flask.make_response('SimplestEndpoint.do_GET', 200)
        return resp

    def do_POST(self, request):
        resp = flask.make_response('SimplestEndpoint.do_POST', 200)
        return resp
    
    def do_DELETE(self, request):
        resp = flask.make_response('SimplestEndpoint.do_DELETE', 200)
        return resp
    
    def do_PATCH(self, request):
        resp = flask.make_response('SimplestEndpoint.do_PATCH', 200)
        return resp



