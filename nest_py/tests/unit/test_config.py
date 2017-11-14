# -*- coding: utf-8 -*-
from nest_py.core.flask.app2 import create_app

from nest_py.nest_envs import RunLevel, ProjectEnv
import nest_py.core.nest_config as nest_config

def test_axiom():
    assert True
    return

def test_dev_config():
    run_level = RunLevel.development_instance()
    project_env = ProjectEnv.knoweng_instance()
    config = nest_config.generate_config(project_env, run_level)
    app = create_app(config, project_env, run_level)
    if app is None:
        assert False, "create_app returned None"

    assert app.config['ENV'] == 'dev'
    assert app.config['DEBUG'] is True
    return

def test_production_config():
    run_level = RunLevel.production_instance()
    project_env = ProjectEnv.knoweng_instance()
    config = nest_config.generate_config(project_env, run_level)
    app = create_app(config, project_env, run_level)
    if app is None:
        assert False, "create_app returned None"

    assert app.config['ENV'] == 'prod'
    assert app.config['DEBUG'] is False
    assert app.config['DEBUG_TB_ENABLED'] is False
    return



