"""Tests nest_py.flask.accounts.authentication.NativeAuthenticationStrategy"""
# -*- coding: utf-8 -*-
import pytest
from flask import Request
from werkzeug.exceptions import UnsupportedMediaType
from werkzeug.test import create_environ
from nest_py.core.flask.accounts.authentication import NativeAuthenticationStrategy

from nest_py.tests.unit.db.test_users import setup_db, finish_up, make_users_db_client
import nest_py.core.db.db_ops_utils as db_ops_utils

class MockApp(object):
    def __init__(self, config):
        self.config = config
        self.config.update({
            'JWT_SECRET': 'secret0',
            'JWT_ISSUER': 'issuer0',
            'JWT_AUDIENCES': ['audience0'],
            'JWT_LIFESPAN': 1.0})
        return

GOOD_USER_CONFIGS = [
        {
            'username': 'demouser',
            'password': 'demopass',
            'given_name': 'Demo',
            'family_name': 'User',
        }, {
            'username': 'otheruser',
            'password': 'otherpass',
            'given_name': 'Other',
            'family_name': 'User',
        }
    ]


GOOD_MOCK_APP = MockApp({'DEMO_AUTHENTICATION_ACCOUNTS': GOOD_USER_CONFIGS})

def test_authenticate():
    """Tests authenticate."""
    setup_db()
    users_db_client = make_users_db_client()
    #use the helper method from seed_users to add our test users to the test db
    db_ops_utils._add_users_from_configs(users_db_client, GOOD_USER_CONFIGS)

    das = NativeAuthenticationStrategy(GOOD_MOCK_APP, users_db_client)

    # no request
    with pytest.raises(AttributeError):
        das.authenticate(None)

    # wrong content type
    # passing a dict as data below will create a form-encoded request
    env = create_environ('/sessions', 'http://localhost:1234', method='POST', \
        data={'username': 'demouser', 'password': 'demopass'})
    with pytest.raises(UnsupportedMediaType):
        das.authenticate(Request(env))

    # correct content type: note the explicit content type and that data no
    # longer receives a dict--it's quoted
    # no username
    env = create_environ('/sessions', 'http://localhost:1234', method='POST', \
        data='{"password": "demopass"}', \
        content_type='application/json')
    assert das.authenticate(Request(env)) is None

    # no password
    env = create_environ('/sessions', 'http://localhost:1234', method='POST', \
        data='{"username": "demouser"}', \
        content_type='application/json')
    assert das.authenticate(Request(env)) is None

    # correct username, incorrect password
    env = create_environ('/sessions', 'http://localhost:1234', method='POST', \
        data='{"username": "demouser", "password": "pass"}', \
        content_type='application/json')
    assert das.authenticate(Request(env)) is None

    # incorrect username, correct password
    env = create_environ('/sessions', 'http://localhost:1234', method='POST', \
        data='{"username": "user", "password": "demopass"}', \
        content_type='application/json')
    assert das.authenticate(Request(env)) is None

    # correct username, correct password
    env = create_environ('/sessions', 'http://localhost:1234', method='POST', \
        data='{"username": "demouser", "password": "demopass"}', \
        content_type='application/json')
    user = das.authenticate(Request(env))
    assert user.get_nest_id() is not None
    assert user.get_username() == "demouser"
    assert user.get_given_name() == "Demo"
    assert user.get_family_name() == "User"

    # correct username, correct password for second account
    env = create_environ('/sessions', 'http://localhost:1234', method='POST', \
        data='{"username": "otheruser", "password": "otherpass"}', \
        content_type='application/json')
    user = das.authenticate(Request(env))
    assert user.get_nest_id() is not None
    assert user.get_username() == "otheruser"
    assert user.get_given_name() == "Other"
    assert user.get_family_name() == "User"
    finish_up()
    return
