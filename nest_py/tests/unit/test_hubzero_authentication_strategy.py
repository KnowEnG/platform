"""Tests nest_py.flask.accounts.knoweng.knoweng_authentication.HubzeroAuthenticationStrategy"""
# -*- coding: utf-8 -*-
import mock
import pytest
from flask import Request
from werkzeug.exceptions import UnsupportedMediaType
from werkzeug.test import create_environ
from nest_py.knoweng.flask.accounts.knoweng_authentication \
    import HubzeroAuthenticationStrategy

from nest_py.tests.unit.db.test_users import setup_db, finish_up, make_users_db_client

class MockApp(object):
    def __init__(self, config):
        self.config = config

GOOD_CONFIG = {
    'JWT_SECRET': 'secret0',
    'JWT_ISSUER': 'issuer0',
    'JWT_AUDIENCES': ['audience0'],
    'JWT_LIFESPAN': 1.0,
    'HUBZERO_APPLICATION_HOST': 'apphost',
    'HUBZERO_DATABASE_HOST': 'dbhost',
    'HUBZERO_DATABASE_USERNAME': 'dbuser',
    'HUBZERO_DATABASE_PASSWORD': 'dbpass',
    'HUBZERO_DATABASE_NAME': 'dbname'}

def test_init():
    """Tests __init__."""

    setup_db()
    users_db_client = make_users_db_client()

    # no app
    with pytest.raises(AttributeError):
        HubzeroAuthenticationStrategy(None, users_db_client)

    # no app host
    config = GOOD_CONFIG.copy()
    del config['HUBZERO_APPLICATION_HOST']
    with pytest.raises(KeyError):
        HubzeroAuthenticationStrategy(MockApp(config), users_db_client)

    # no db host
    config = GOOD_CONFIG.copy()
    del config['HUBZERO_DATABASE_HOST']
    with pytest.raises(KeyError):
        HubzeroAuthenticationStrategy(MockApp(config), users_db_client)

    # no user
    config = GOOD_CONFIG.copy()
    del config['HUBZERO_DATABASE_USERNAME']
    with pytest.raises(KeyError):
        HubzeroAuthenticationStrategy(MockApp(config), users_db_client)

    # no pass
    config = GOOD_CONFIG.copy()
    del config['HUBZERO_DATABASE_PASSWORD']
    with pytest.raises(KeyError):
        HubzeroAuthenticationStrategy(MockApp(config), users_db_client)

    # no name
    config = GOOD_CONFIG.copy()
    del config['HUBZERO_DATABASE_NAME']
    with pytest.raises(KeyError):
        HubzeroAuthenticationStrategy(MockApp(config), users_db_client)

    # empty app host
    config = GOOD_CONFIG.copy()
    config['HUBZERO_APPLICATION_HOST'] = ''
    with pytest.raises(AttributeError) as exc:
        HubzeroAuthenticationStrategy(MockApp(config), users_db_client)
        assert str(exc.value) == 'HUBZERO_APPLICATION_HOST cannot be empty'

    # empty db host
    config = GOOD_CONFIG.copy()
    config['HUBZERO_DATABASE_HOST'] = ''
    with pytest.raises(AttributeError) as exc:
        HubzeroAuthenticationStrategy(MockApp(config), users_db_client)
        assert str(exc.value) == 'HUBZERO_DATABASE_HOST cannot be empty'

    # empty user
    config = GOOD_CONFIG.copy()
    config['HUBZERO_DATABASE_USERNAME'] = ''
    with pytest.raises(AttributeError) as exc:
        HubzeroAuthenticationStrategy(MockApp(config), users_db_client)
        assert str(exc.value) == 'HUBZERO_DATABASE_USERNAME cannot be empty'

    # empty pass
    config = GOOD_CONFIG.copy()
    config['HUBZERO_DATABASE_PASSWORD'] = ''
    with pytest.raises(AttributeError) as exc:
        HubzeroAuthenticationStrategy(MockApp(config), users_db_client)
        assert str(exc.value) == 'HUBZERO_DATABASE_PASSWORD cannot be empty'

    # empty name
    config = GOOD_CONFIG.copy()
    config['HUBZERO_DATABASE_NAME'] = ''
    with pytest.raises(AttributeError) as exc:
        HubzeroAuthenticationStrategy(MockApp(config), users_db_client)
        assert str(exc.value) == 'HUBZERO_DATABASE_NAME cannot be empty'

    # app host with space
    config = GOOD_CONFIG.copy()
    config['HUBZERO_APPLICATION_HOST'] += ' '
    with pytest.raises(AttributeError) as exc:
        HubzeroAuthenticationStrategy(MockApp(config), users_db_client)
        assert str(exc.value) == \
            'HUBZERO_APPLICATION_HOST cannot contain spaces'

    # db host with space
    config = GOOD_CONFIG.copy()
    config['HUBZERO_DATABASE_HOST'] += ' '
    with pytest.raises(AttributeError) as exc:
        HubzeroAuthenticationStrategy(MockApp(config), users_db_client)
        assert str(exc.value) == \
            'HUBZERO_DATABASE_HOST cannot contain spaces'

    # user with space
    config = GOOD_CONFIG.copy()
    config['HUBZERO_DATABASE_USERNAME'] += ' '
    with pytest.raises(AttributeError) as exc:
        HubzeroAuthenticationStrategy(MockApp(config), users_db_client)
        assert str(exc.value) == \
            'HUBZERO_DATABASE_USERNAME cannot contain spaces'

    # pass with space
    config = GOOD_CONFIG.copy()
    config['HUBZERO_DATABASE_PASSWORD'] += ' '
    with pytest.raises(AttributeError) as exc:
        HubzeroAuthenticationStrategy(MockApp(config), users_db_client)
        assert str(exc.value) == \
            'HUBZERO_DATABASE_PASSWORD cannot contain spaces'

    # name with space
    config = GOOD_CONFIG.copy()
    config['HUBZERO_DATABASE_NAME'] += ' '
    with pytest.raises(AttributeError) as exc:
        HubzeroAuthenticationStrategy(MockApp(config), users_db_client)
        assert str(exc.value) == \
            'HUBZERO_DATABASE_NAME cannot contain spaces'

    # good username and password
    HubzeroAuthenticationStrategy(MockApp(GOOD_CONFIG), users_db_client)
    finish_up()
    return

def test_authenticate():
    """Tests authenticate."""

    setup_db()
    users_db_client = make_users_db_client()

    has = HubzeroAuthenticationStrategy(MockApp(GOOD_CONFIG), users_db_client)

    # no request
    with pytest.raises(AttributeError):
        has.authenticate(None)

    # wrong content type
    # passing a dict as data below will create a form-encoded request
    env = create_environ('/sessions', 'http://localhost:1234', method='POST', \
        data={'hz_session': 'gibberish'})
    with pytest.raises(UnsupportedMediaType):
        has.authenticate(Request(env))

    # correct content type: note the explicit content type and that data no
    # longer receives a dict--it's quoted
    # no hz_session
    env = create_environ('/sessions', 'http://localhost:1234', method='POST', \
        data='{"other": "whatever"}', content_type='application/json')
    assert has.authenticate(Request(env)) is None

    # mock db condition: no match for hz_session
    with mock.patch('nest_py.knoweng.flask.accounts.knoweng_authentication.' + \
        'HubzeroAuthenticationStrategy.fetch_session', return_value=None):
        env = create_environ('/sessions', 'http://localhost:1234', \
            method='POST', data='{"hz_session": "gibberish"}', \
            content_type='application/json')
        assert has.authenticate(Request(env)) is None

    # mock db condition: match for hz_session
    with mock.patch('nest_py.knoweng.flask.accounts.knoweng_authentication.' + \
        'HubzeroAuthenticationStrategy.fetch_session', return_value={\
            u'userid': '150',
            u'username': 'hzuser',
            u'givenName': 'HUBZero',
            u'surname': 'User',
            u'picture': 'profile.png'}):
        env = create_environ('/sessions', 'http://localhost:1234', \
            method='POST', data='{"hz_session": "gibberish"}', \
            content_type='application/json')
        user = has.authenticate(Request(env))
        assert user.get_nest_id() is not None
        assert user.get_username() == "hzuser"
        assert user.get_given_name() == "HUBZero"
        assert user.get_family_name() == "User"
        assert user.get_external_id() == "150"
        assert user.get_origin() == "hubzero"
        assert user.get_thumb_url() == \
            "http://apphost/members/150/Image:thumb.png"

    finish_up()
    return
