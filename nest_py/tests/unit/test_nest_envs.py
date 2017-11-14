# -*- coding: utf-8 -*-
import os
import pytest
from nest_py.nest_envs import ProjectEnv, RunLevel

def test_project_os_roundtrip():
    #delete PROJECT_ENV if it's currently set
    os.environ.pop("PROJECT_ENV", None)

    env_obs = ProjectEnv.detect_from_os()
    assert env_obs == None
    
    env_obs = ProjectEnv.detect_from_os(fallback_to_default=True)
    assert env_obs == ProjectEnv.default_instance()

    env1 = ProjectEnv.default_instance()
    assert not env1 == None 
    env1.write_to_os()
    env_obs = ProjectEnv.detect_from_os()
    assert env1 == env_obs
    
    env_obs = ProjectEnv.detect_from_os(fallback_to_default=True)
    assert env1 == env_obs
    return

def test_project_instances():
    knoweng_env = ProjectEnv.knoweng_instance()
    mmbdb_env = ProjectEnv.mmbdb_instance()

    knoweng_rt = ProjectEnv(knoweng_env.get_project_name())
    mmbdb_rt = ProjectEnv(mmbdb_env.get_project_name())

    assert knoweng_env == knoweng_rt
    assert knoweng_env == knoweng_env
    assert not knoweng_env == mmbdb_env
    assert mmbdb_env == mmbdb_rt

    s = (str(knoweng_env))
    print(s)
    assert s.endswith('knoweng')

    assert knoweng_env == ProjectEnv.from_string('KnowEng')
    return

def test_project_bad_name():
    with pytest.raises(Exception):
        env = ProjectEnv("not a real project name")

    empty_env = ProjectEnv.from_string('')
    assert empty_env == None
    return
        
def test_deploy_os_roundtrip():
    #delete Deploy_ENV if it's currently set
    os.environ.pop("DEPLOY_ENV", None)
    
    env_obs = RunLevel.detect_from_os()
    assert env_obs == None
    
    env_obs = RunLevel.detect_from_os(fallback_to_default=True)
    assert env_obs == RunLevel.default_instance()

    env1 = RunLevel.default_instance()
    assert not env1 == None
    env1.write_to_os()
    env_obs = RunLevel.detect_from_os()
    assert env1 == env_obs
    return

def test_deploy_instances():
    development_env = RunLevel.development_instance()
    production_env = RunLevel.production_instance()

    development_rt = RunLevel(development_env.get_runlevel_name())
    production_rt = RunLevel(production_env.get_runlevel_name())

    assert development_env == development_rt
    assert development_env == development_env
    assert not development_env == production_env
    assert production_env == production_rt

    s = (str(development_env))
    print(s)
    assert s.endswith('development')

    assert development_env == RunLevel('development')
    return

def test_deploy_bad_name():
    with pytest.raises(Exception):
        env = RunLevel("not a real Deploy name")
    return

