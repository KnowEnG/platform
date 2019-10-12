"""Tests nest_py.knoweng.flask.accounts.knoweng_authentication.CILogonAuthenticationStrategy"""
# -*- coding: utf-8 -*-
import responses
import pytest
from flask import Request
from werkzeug.exceptions import UnsupportedMediaType
from werkzeug.test import create_environ
from nest_py.knoweng.flask.accounts.knoweng_authentication \
    import CILogonAuthenticationStrategy

from nest_py.tests.unit.db.test_users import setup_db, finish_up, make_users_db_client

class MockApp(object):
    def __init__(self, config):
        self.config = config

GOOD_CONFIG = {
    'JWT_SECRET': 'secret0',
    'JWT_ISSUER': 'issuer0',
    'JWT_AUDIENCES': ['audience0'],
    'JWT_LIFESPAN': 1.0,
    'CILOGON_CLIENT_ID': 'thisismyfakeclientid',
    'CILOGON_CLIENT_SECRET': 'thisismyfakeclientsecret',
    'CILOGON_REDIRECT_URI': 'https://fakesite.com/static/index.html'}

def test_init():
    """Tests __init__."""

    setup_db()
    users_db_client = make_users_db_client()

    # no app
    with pytest.raises(AttributeError):
        CILogonAuthenticationStrategy(None, users_db_client)

    # no client id
    config = GOOD_CONFIG.copy()
    del config['CILOGON_CLIENT_ID']
    with pytest.raises(KeyError):
        CILogonAuthenticationStrategy(MockApp(config), users_db_client)

    # no client secret
    config = GOOD_CONFIG.copy()
    del config['CILOGON_CLIENT_SECRET']
    with pytest.raises(KeyError):
        CILogonAuthenticationStrategy(MockApp(config), users_db_client)

    # no redirect uri
    config = GOOD_CONFIG.copy()
    del config['CILOGON_REDIRECT_URI']
    with pytest.raises(KeyError):
        CILogonAuthenticationStrategy(MockApp(config), users_db_client)

    # empty client id
    config = GOOD_CONFIG.copy()
    config['CILOGON_CLIENT_ID'] = ''
    with pytest.raises(AttributeError) as exc:
        CILogonAuthenticationStrategy(MockApp(config), users_db_client)
        assert str(exc.value) == 'CILOGON_CLIENT_ID cannot be empty'

    # empty client secret
    config = GOOD_CONFIG.copy()
    config['CILOGON_CLIENT_SECRET'] = ''
    with pytest.raises(AttributeError) as exc:
        CILogonAuthenticationStrategy(MockApp(config), users_db_client)
        assert str(exc.value) == 'CILOGON_CLIENT_SECRET cannot be empty'

    # empty redirect uri
    config = GOOD_CONFIG.copy()
    config['CILOGON_REDIRECT_URI'] = ''
    with pytest.raises(AttributeError) as exc:
        CILogonAuthenticationStrategy(MockApp(config), users_db_client)
        assert str(exc.value) == 'CILOGON_REDIRECT_URI cannot be empty'

    # client id with space
    config = GOOD_CONFIG.copy()
    config['CILOGON_CLIENT_ID'] += ' '
    with pytest.raises(AttributeError) as exc:
        CILogonAuthenticationStrategy(MockApp(config), users_db_client)
        assert str(exc.value) == \
            'CILOGON_CLIENT_ID cannot contain spaces'

    # client secret with space
    config = GOOD_CONFIG.copy()
    config['CILOGON_CLIENT_SECRET'] += ' '
    with pytest.raises(AttributeError) as exc:
        CILogonAuthenticationStrategy(MockApp(config), users_db_client)
        assert str(exc.value) == \
            'CILOGON_CLIENT_SECRET cannot contain spaces'

    # redirect uri with space
    config = GOOD_CONFIG.copy()
    config['CILOGON_REDIRECT_URI'] += ' '
    with pytest.raises(AttributeError) as exc:
        CILogonAuthenticationStrategy(MockApp(config), users_db_client)
        assert str(exc.value) == \
            'CILOGON_REDIRECT_URI cannot contain spaces'

    # good values
    CILogonAuthenticationStrategy(MockApp(GOOD_CONFIG), users_db_client)
    finish_up()
    return

def test_authenticate():
    """Tests authenticate."""

    setup_db()
    users_db_client = make_users_db_client()

    has = CILogonAuthenticationStrategy(MockApp(GOOD_CONFIG), users_db_client)

    # no request
    with pytest.raises(AttributeError):
        has.authenticate(None)

    # wrong content type
    # passing a dict as data below will create a form-encoded request
    env = create_environ('/sessions', 'http://localhost:1234', method='POST', \
        data={'authCode': 'gibberish'})
    with pytest.raises(UnsupportedMediaType):
        has.authenticate(Request(env))

    # correct content type: note the explicit content type and that data no
    # longer receives a dict--it's quoted
    # no authCode
    env = create_environ('/sessions', 'http://localhost:1234', method='POST', \
        data='{"other": "whatever"}', content_type='application/json')
    assert has.authenticate(Request(env)) is None

    # mock request condition: no match for authCode
    with responses.RequestsMock() as rsps:
        json = {
            "error":"invalid_request",
            "error_description":"No pending transaction found for id=gibberish"
        }
        # pylint: disable=no-member
        rsps.add(responses.POST, "https://cilogon.org/oauth2/token", \
            json=json, status=400)
        # pylint: enable=no-member
        env = create_environ('/sessions', 'http://localhost:1234', \
            method='POST', data='{"authCode": "gibberish"}', \
            content_type='application/json')
        assert has.authenticate(Request(env)) is None

    # mock request condition: match for authCode
    with responses.RequestsMock() as rsps:
        json1 = {
            "access_token": "fakeaccesstoken",
            "id_token": "fakeidtoken",
            "token_type": "Bearer"
        }
        json2 = {
            "sub": "fakesub",
            "aud":"fakeaud",
            "iss":"https://cilogon.org",
            "given_name":"John",
            "family_name":"Smith",
            "email":"jsmith@illinois.edu"
        }
        # pylint: disable=no-member
        rsps.add(responses.POST, "https://cilogon.org/oauth2/token", \
            json=json1, status=200)
        rsps.add(responses.POST, "https://cilogon.org/oauth2/userinfo", \
            json=json2, status=200)
        # pylint: enable=no-member
        env = create_environ('/sessions', 'http://localhost:1234', \
            method='POST', data='{"authCode": "gibberish"}', \
            content_type='application/json')
        user = has.authenticate(Request(env))
        assert user.get_nest_id() is not None
        assert user.get_username() == "jsmith@illinois.edu"
        assert user.get_given_name() == "John"
        assert user.get_family_name() == "Smith"
        assert user.get_external_id() == "fakesub"
        assert user.get_origin() == "https://cilogon.org"
        assert user.get_thumb_url() == ''

    finish_up()
    return
