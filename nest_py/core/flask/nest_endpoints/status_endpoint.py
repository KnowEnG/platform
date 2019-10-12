import os

from git import Repo
from git.exc import InvalidGitRepositoryError
import flask

from nest_py.core.flask.nest_endpoints.nest_endpoint import NestEndpoint

class StatusEndpoint(NestEndpoint):
    """Provides system status."""

    def __init__(self, authenticator):
        relative_url = 'status'
        super(StatusEndpoint, self).__init__(relative_url, authenticator)
        return

    def get_flask_rule(self):
        return 'status'

    def get_flask_endpoint(self):
        return 'status'

    def handle_request(self, **kwargs):
        request = flask.request #this is a global

        jdata = dict()

        # we'll ask git for the sha if we can
        # some knoweng deployments use public docker images that don't contain
        # the .git directory, so in that case, we'll fall back to reading a
        # .git-sha file created for us by the build process
        try:
            repo = Repo(search_parent_directories=True)
            jdata['sha'] = repo.head.object.hexsha
        except InvalidGitRepositoryError:
            with open('/code_live/.git-sha', 'r') as shafile:
                jdata['sha'] = shafile.read().rstrip()

        jdata['runlevel'] = os.environ['NEST_RUNLEVEL']

        app_config = flask.current_app.config
        jdata['cilogonLoginUrl'] = app_config['CILOGON_LOGIN_URL'] if \
            app_config['CILOGON_ENABLED'] else ''
        jdata['maxUploadSize'] = app_config['MAX_CONTENT_LENGTH']
        resp = self._make_success_json_response(jdata)
        return resp
