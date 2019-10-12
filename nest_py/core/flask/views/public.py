# -*- coding: utf-8 -*-
"""Public section, including homepage and signup."""
import json
import flask
from flask import Blueprint, redirect

BLUEPRINT = Blueprint('public', __name__, static_folder="../static",\
    template_folder="../templates")

#TODO: pull this out of flask.config dynamically
API_PREFIX = '/api/v2/'

@BLUEPRINT.route("/", methods=["GET"])
def home():
    """Renders the home page.
       Note that nginx serves '/static/' directly, but does
       not do the redirect from '/' to '/static/index.html'
    """
    return redirect('/static/index.html')

@BLUEPRINT.route(API_PREFIX + 'heartbeat', methods=["GET"])
def heartbeat():
    """Simple endpoint to tell the world flask is alive
    
    """
    print('Got heartbeat with method: ' + flask.request.method)
    jdata = {'message': 'hello from heartbeat'}
    payload = json.dumps(jdata)
    resp = flask.make_response(payload, 200)
    resp.headers['Content-Type'] = 'application/json'
    return resp
