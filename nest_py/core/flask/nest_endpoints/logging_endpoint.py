import json
import logging
import flask

from nest_py.core.flask.nest_endpoints.nest_endpoint import NestEndpoint

# create a logger named 'client'
logger = logging.getLogger('client')
logger.setLevel(logging.DEBUG)

# create file handler which logs even debug messages
fh = logging.FileHandler('client-debug.log')
fh.setLevel(logging.DEBUG)

# create console handler with a higher log level
ch = logging.StreamHandler()
ch.setLevel(logging.WARN)

# create formatter and add it to the handlers
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
ch.setFormatter(formatter)

# add the handlers to the logger
logger.addHandler(ch)
logger.addHandler(fh)

# define a convenience wrapper for the convenience wrappers
LOGMUX = { "debug": logger.debug, "info": logger.info, "warn": logger.warn, "error": logger.error, "critical": logger.critical }


class LoggingEndpoint(NestEndpoint):

    def __init__(self, authenticator):
    
        self.flask_ep = 'logs'
        self.flask_rule = 'logs'
        #TODO:We aren't requiring the user be logged in so we can
        #capture errors at the login/logout screens, but that might be a
        #bad idea if we ever let people outside the firewall access 
        #a nest app
        require_auth = False
        super(LoggingEndpoint, self).__init__(self.flask_ep, 
            authenticator, require_auth=require_auth)
        return 

    def get_flask_rule(self):
        return self.flask_rule

    def get_flask_endpoint(self):
        return self.flask_ep

    def do_POST(self, request, requesting_user):
        """
        called when someone POSTs a message to the 'logs' endpoint

        """
        # Scrape some relevant fields from the request data
        # TODO: Scrape other useful things? UserAgent? Duration?
        request_data = json.loads(request.data)
        level = request_data.get('level', 'debug')
        message = request_data.get('message', 'blank')
        stack = request_data.get('stack')
        sent = request_data.get('sent')
        ip = request.remote_addr
        
        if requesting_user is None:
            username = 'NOT_LOGGED_IN'
        else:
            username = requesting_user.get_username()
        
        # Format and log the message to filehandler and consolehandler, as defined above
        message_prefix = ip + " (" + username +") - "
        LOGMUX[level](message_prefix + message)
        
        # Log stack trace, if one was given
        if stack is not None:
            LOGMUX[level](message_prefix + "Stack Trace:\n" + stack)
        #pylint: enable=unused-argument
        resp = flask.make_response('logged ok', 200)
        return resp
        

