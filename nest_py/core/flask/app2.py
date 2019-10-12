import logging

import flask
from flask import render_template
from flask_sqlalchemy import SQLAlchemy

from nest_py.core.db.sqla_resources import FlaskSqlaResources
from nest_py.nest_envs import ProjectEnv, RunLevel
import nest_py.core.nest_config as nest_config
import nest_py.core.db.nest_db as nest_db
import nest_py.core.db.core_db as core_db
import nest_py.core.db.sqla_resources as sqla_resources
from nest_py.core.flask.views import public
from nest_py.core.flask.extensions import (
    DEBUG_TOOLBAR,
)

logging.basicConfig()

#TODO: move to flask.config
API_PREFIX = '/api/v2/'

def make_flask_app():
    project_env = ProjectEnv.detect_from_os(fallback_to_default=True)
    runlevel = RunLevel.detect_from_os(fallback_to_default=True)
    config = nest_config.generate_config(project_env, runlevel)
    print('make flask app:  ' + str(project_env) + '  ' + str(runlevel))
    app = create_app(config, project_env, runlevel)
    return app

def create_app(config, project_env, runlevel):
    app = flask.Flask('nest')
    app.config.update(**config)
    setup_db(app, project_env)
    authenticator = build_authenticator(app, project_env, runlevel)
    with app.app_context():
        register_nest_endpoints(app, project_env, authenticator)
        register_extensions(app)
        register_blueprints(app)
        register_errorhandlers(app)
    return app

def setup_db(flask_app, project_env):
    db_config = nest_db.generate_db_config(project_env=project_env)
    flask_app.config['SQLALCHEMY_DATABASE_URI'] = sqla_resources.get_engine_url(db_config)
    db = SQLAlchemy(flask_app)
    sqla_res= FlaskSqlaResources(db, db_config)
    # FIXME flask still uses JobsSqlaResources, despite all this
    # see https://visualanalytics.atlassian.net/browse/TOOL-510
    # nest_db.set_global_sqla_resources(sqla_res)
    return

def build_authenticator(flask_app, project_env, runlevel):
    users_sqla_maker = core_db.get_nest_users_sqla_maker()
    db_engine = nest_db.get_global_sqlalchemy_engine()
    md = nest_db.get_global_sqlalchemy_metadata()
    users_client = users_sqla_maker.get_db_client(db_engine, md)

    #the authenticator will interact with the local db as the master system_user
    auth_user = core_db.get_system_user()
    users_client.set_requesting_user(auth_user)

    # knoweng uses CILogon to look up user accounts in production
    # note the CILogon code could be moved to core for use w/ other projects
    # all other situations will use user accounts stored in the local db
    use_cilogon = flask_app.config.get('CILOGON_ENABLED', False)

    if use_cilogon:
        print('registering CILogon authenticator')
        from nest_py.knoweng.flask.accounts.knoweng_authentication \
            import CILogonAuthenticationStrategy
        authenticator = CILogonAuthenticationStrategy(flask_app, users_client)
    else:
        from nest_py.core.flask.accounts.authentication \
            import NativeAuthenticationStrategy
        authenticator = NativeAuthenticationStrategy(
            flask_app, users_client)
    return authenticator

def register_nest_endpoints(flask_app, project_env, authenticator):
    db_engine = nest_db.get_global_sqlalchemy_engine()
    sqla_md = nest_db.get_global_sqlalchemy_metadata()
    if ProjectEnv.hello_world_instance() == project_env:
        import nest_py.hello_world.flask.hw_flask as hw_flask
        nest_endpoints = hw_flask.get_nest_endpoints(
            db_engine, sqla_md, authenticator)
    elif ProjectEnv.mmbdb_instance() == project_env:
        import nest_py.omix.flask.omix_flask as omix_flask
        nest_endpoints = omix_flask.get_nest_endpoints(
            db_engine, sqla_md, authenticator)
    elif ProjectEnv.knoweng_instance() == project_env:
        import nest_py.knoweng.flask.knoweng_flask as knoweng_flask
        nest_endpoints = knoweng_flask.get_nest_endpoints(
            db_engine, sqla_md, authenticator)
    else:
        raise Exception("Unknown project when registering endpoints")

    for flask_ep in nest_endpoints.get_flask_endpoints():
        nest_ep = nest_endpoints.get_endpoint(flask_ep)
        relative_flask_rule = nest_ep.get_flask_rule()
        rule = API_PREFIX + relative_flask_rule
        print('registering flask rule: ' + str(rule))
        flask_ep = nest_ep.get_flask_endpoint()
        renderer = nest_ep.handle_request
        flask_app.add_url_rule(rule, flask_ep, view_func=renderer, \
            methods=['GET', 'POST', 'PATCH', 'DELETE'])
    return

def register_extensions(app):
    """Initialize extensions (including assets).

    Args:
        app (Eve): The Eve application object.

    Returns:
        None: None.

    """
    DEBUG_TOOLBAR.init_app(app)
    return None

def register_blueprints(app):
    """Register Flask blueprints.

    Args:
        app (Eve): The Eve application object.

    Returns:
        None: None.

    """
    app.register_blueprint(public.BLUEPRINT)
    return None

def register_errorhandlers(app):
    """Register error handlers for HTTP error codes.

    Args:
        app (Eve): The Eve application object.

    Returns:
        None: None.

    """
    def render_error(error):
        """Render a template named for the error's HTTP error code.

        Args:
            error (Exception): The error.

        Returns:
            None: None.

        """
        # If a HTTPException, pull the `code` attribute; default to 500
        error_code = getattr(error, 'code', 500)
        return render_template("{0}.html".format(error_code)), error_code
    for errcode in [401, 404, 500]:
        app.errorhandler(errcode)(render_error)
    return None

app = make_flask_app()
