# -*- coding: utf-8 -*-
"""Defines fixtures available to all tests."""

import pytest
from webtest import TestApp

from nest_py.nest_envs import RunLevel, ProjectEnv
import nest_py.core.nest_config as nest_config

from nest_py.ops.nest_sites import NestSite

@pytest.yield_fixture(scope='function')
def app():
    from nest_py.core.flask.app2 import create_app
    run_level = RunLevel.development_instance()
    project_env = ProjectEnv.knoweng_instance()
    config = nest_config.generate_config(run_level, project_env)
    #force localhost as the db server
    host = NestSite.localhost_instance().get_server_ip_address()
    config['host'] = host
    _app = create_app(config, project_env, run_level)
    ctx = _app.test_request_context()
    ctx.push()

    yield _app

    ctx.pop()


@pytest.fixture(scope='function')
def testapp(app):
    """A Webtest app."""
    return TestApp(app)


#@pytest.yield_fixture(scope='function')
#def db(app):
#    _db.app = app
#    with app.app_context():
#        _db.create_all()
#
#    yield _db
#
#    _db.drop_all()


#@pytest.fixture
#def user(db):
#    user = UserFactory(password='myprecious')
#    db.session.commit()
#    return user
