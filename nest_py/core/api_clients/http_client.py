import json
import traceback
import time
from requests import Session
from requests import Request
from requests.exceptions import Timeout
from requests.exceptions import ConnectionError

#import nest_py.flask.app2.API_PREFIX as API_PREFIX
#TODO move to a (jobs?) config file
API_PREFIX = '/api/v2/'

VERBOSE = False #log full request and responses

class NestHttpClient(object):
    """
    Does basic GET,POST,PATCH,DELETE with Nest error handling and logging.
    Is specific to calling a nest API.
    """

    def __init__(self, server_address='localhost', server_port=80,
        auth_token=None):
        self.server = server_address
        self.port = server_port
        self.session = Session()
        self.auth_token = auth_token
        return

    def login(self, username, password):
        """
        causes a call to the server to get a jwt token which
        will be used for this NestHttpClient's life (or until
        this is called again)
        """
        http_data = {'username': username, 'password': password}
        request = NestHttpRequest('sessions',
            op='POST',
            data=http_data,
            num_tries=1,
            timeout_secs=3.0)
        response = self.perform_request(request)
        if response.did_succeed():
            token = response.get_data_payload_as_jdata()['access_token']
            self.auth_token = token
        else:
            raise Exception("Failed to login as user: " + username)
        return 

    def set_auth_token(self, auth_token):
        self.auth_token = auth_token
        return

    def logout(self):
        self.auth_token = None
        return

    def perform_request(self, nest_request, verbose_errors=True):

        url = self._make_nest_api_url(nest_request)
        data_payload = None
        http_code = None
        exception = None
        headers = None

        num_tries = nest_request.get_num_tries()
        no_success = True
        while num_tries > 0 and no_success:

            #if not our first try, wait for the delay period
            if num_tries != nest_request.get_num_tries():
                time.sleep(nest_request.get_retry_delay_secs())

            num_tries = num_tries - 1
            try:
                headers = nest_request.get_headers()
                # set the optional auth_token
                if self.auth_token is not None:
                    headers = headers.copy() # don't modify caller's object
                    headers['Authorization'] = 'Bearer ' + self.auth_token

                ##see http://docs.python-requests.org/en/latest/user/advanced/#request-and-response-objects
                request = Request(
                        nest_request.get_http_op(),
                        url,
                        data=nest_request.get_data_payload(),
                        files=nest_request.get_files_payload(),
                        headers=headers,
                        params=nest_request.get_query_params(),
                        )
                prepped_request = self.session.prepare_request(request)
                op = nest_request.get_http_op()
                full_url = prepped_request.url
                if VERBOSE:
                    log(op + ': ' + str(full_url))
                    log('request body: ')
                    log(str(nest_request.get_data_payload()))
                resp = self.session.send(prepped_request,
                        timeout=nest_request.get_timeout_secs(),
                        allow_redirects=True,
                        verify=False
                    )
                data_payload = resp.text
                if VERBOSE:
                    log('response code: ' + str(resp.status_code))
                    if resp.headers['Content-Type'] == 'text/html; charset=utf-8':
                        log('response body:  <<supressing html response>>')
                    else:
                        log('reponse body: ' + resp.text)
                http_code = resp.status_code
                headers = resp.headers
            except Timeout as te:
                exception = te
            except ConnectionError as te:
                exception = te
            except Exception as e:
                traceback.print_exc()
                exception = e

            nest_response = NestHttpResponse(nest_request,
                http_code=http_code,
                exception=exception,
                data_payload=data_payload,
                headers=headers)

            if nest_response.did_succeed():
                no_success = False
            else:
                if verbose_errors:
                    log(nest_response.get_error_message())
                    log("num tries remaining: " + str(num_tries))

        return nest_response

    def _make_nest_api_url(self, nest_request):
        """
        constructs a url against the api of a nest server
        running at the server:port defined in this client.
        NOTE: the 'api' prefix is defined by the URL_PREFIX
            parameter in the Eve config.
        """
        url = 'https://'
        url += str(self.server)
        url += API_PREFIX
        url += str(nest_request.get_relative_url())
        return url

class NestHttpRequest(object):

    def __init__(self, relative_url, op="GET", http_params=None,\
           headers=None, data=None, files=None, require_json=True,
           timeout_secs=60.0, num_tries=3, retry_delay_secs=1.0):
        """

        headers(dict of String->String) will be merged with a set of default
            headers
        files is a dictionary of {<file field name>: <fileobject>} files to
            upload. If files is None, data will be converted to JSON for an
            application/json request. If files is not None, data and files
            will be encoded as multipart/form-data.
        If require_json, the header accept type will be set to JSON and the returned
            payload will be parsed as json. If the parsing does not succeed, will
            be considered a failed call
        timeout_secs is how many seconds to try to initialize a connection, not total
            download time
        num_tries is how many attempts will be made if the request errors out for
            any reason (may be more intelligent in the future).
        retry_delay_secs how many seconds to wait between tries
        """
        if http_params is None:
            http_params = {}
        if headers is None:
            headers = {}
        self.relative_url = relative_url
        if op in ["GET", "POST", "PATCH", "DELETE"]:
            self.http_op = op
        else:
            raise Exception('unsupported http op: ' + str(op))

        self.http_params = http_params
        self.require_json = require_json
        self.data = data
        self.files = files
        self.timeout_secs = timeout_secs
        self.num_tries = num_tries
        self.retry_delay_secs = retry_delay_secs

        self.headers = dict()
        #defaults for talking to a nest server
        if files is None:
            self.headers['Content-Type'] = 'application/json'
            self.data = json.dumps(data)
        # if files is not None, then we have to use multipart/form-data
        # that means self.data should not be JSON-encoded
        # the Content-Type will be set automatically and will include the
        #     correct boundary, which we can't hardcode

        #headers we got as an input, allowed to overwrite defaults
        for header_key in headers:
            self.headers[header_key] = headers[header_key]

        return

    def get_http_op(self):
        return self.http_op

    def get_data_payload(self):
        return self.data

    def get_files_payload(self):
        return self.files

    def get_relative_url(self):
        return self.relative_url

    def get_query_params(self):
        return self.http_params

    def get_headers(self):
        return self.headers

    def get_require_json(self):
        return self.require_json

    def get_timeout_secs(self):
        return self.timeout_secs

    def get_num_tries(self):
        return self.num_tries

    def get_retry_delay_secs(self):
        return self.retry_delay_secs

class NestHttpResponse(object):

    def __init__(self, request, http_code=None, exception=None, data_payload=None,
        headers=None):
        """
        request(NestHttpRequest) the originating request
        http_code(integer) http status code, or None if the call failed altogether
        exception(Exception) if the call failed completely, the exception
        data_payload(String) if the call got a response from the server, the
            body of the message as plain text
        headers(dict of String->String) headers that came back with the response,
            or None if the call failed altogether

        """
        self.request = request
        self.http_code = http_code
        self.exception = exception
        self.data_payload = data_payload
        self.headers = headers
        self.jdata_payload = None

        self._process_jdata_payload()
        return

    def _process_jdata_payload(self):
        if self.http_did_succeed() and self.request.get_require_json() \
                and (self.data_payload is not None):
            try:
                self.jdata_payload = json.loads(self.data_payload)
            except Exception as e:
                traceback.print_exc()
                self.exception = e
        return

    def get_data_payload(self):
        return self.data_payload

    def get_data_payload_as_jdata(self):
        return self.jdata_payload

    def get_http_code(self):
        return self.http_code

    def did_succeed(self):
        if self.http_did_succeed():
            succeeded = True
            if self.request.get_require_json():
                if self.jdata_payload is None:
                    succeeded = False
        else:
            succeeded = False
        return succeeded

    def http_did_succeed(self):
        return self.http_code >= 200 and self.http_code < 300

    def get_error_message(self):
        if self.exception is not None:
            msg = str(self.exception)
        else:
            msg = "http code was: " + str(self.http_code)
            if self.http_code != 404:#don't need to log entire 404 html page
                msg += '\n' + self.data_payload.encode('ascii', 'replace')
        return msg

def log(msg):
    #print(msg.encode('ascii', 'replace'))
    print(msg.encode('utf-8'))
    return
