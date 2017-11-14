""" 
Below are the config definitions for various environments and projects that
need to be bundled into the main config dictionary that flask consumes on
startup
"""

from datetime import timedelta
import os
from nest_py.nest_envs import ProjectEnv, RunLevel

def generate_config_from_os():
    """
    Determines runlevel and project_env from environment variables, then
    returns generate_eve_config(project_env, runlevel).
    """
    project_env = ProjectEnv.detect_from_os(fallback_to_default=True)
    print "Detected PROJECT_ENV: " + str(project_env)

    runlevel = RunLevel.detect_from_os(fallback_to_default=True)
    print "Detected RUN_LEVEL: " + str(runlevel)

    return generate_config(project_env, runlevel)

def generate_config(project_env, runlevel):
    """
    runlevel (RunLevel)
    project_env (ProjectEnv)
    """
    config = {}
    base_config = _generate_base_config()
    config.update(base_config)
    deploy_config = _generate_deploy_params(runlevel)
    config.update(deploy_config)
    project_config = _generate_project_params(project_env, runlevel)
    config.update(project_config)
    seed_users = generate_seed_users(project_env, runlevel)
    config['seed_users'] = seed_users
    return config

def _generate_project_params(project_env, runlevel):
    if project_env == ProjectEnv.hello_world_instance():
        import nest_py.hello_world.hw_config as hw_config
        project_params = hw_config.generate_project_params(runlevel)
    elif project_env == ProjectEnv.knoweng_instance():
        import nest_py.knoweng.knoweng_config as knoweng_config
        project_params = knoweng_config.generate_project_params(runlevel)
    elif project_env == ProjectEnv.mmbdb_instance():
        import nest_py.omix.omix_config as omix_config
        project_params = omix_config.generate_project_params(runlevel)
    else:
        raise Exception("Unsupported project env: " + str(project_env))
    return project_params

def _generate_deploy_params(runlevel):
    if runlevel == RunLevel.development_instance():
        supplemental_config = _generate_development_params()
    elif runlevel == RunLevel.production_instance():
        supplemental_config = _generate_production_params()
    else:
        raise Exception("Unsupported runlevel: " + str(runlevel))
    return supplemental_config

def _generate_base_config():
    #TODO: break this up by component that uses them. 
    #Hard to know what is still being used like this
    config = {
        "SECRET_KEY": 'GARBAGESECRET',
        # APP_DIR is this directory
        "APP_DIR": os.path.abspath(os.path.dirname(__file__)),
        "PROJECT_ROOT": os.path.abspath(
            os.path.join(
                os.path.abspath(os.path.dirname(__file__)), os.pardir)),
        "BCRYPT_LOG_ROUNDS": 13,
        "DEBUG_TB_ENABLED": False,  # Disable Debug toolbar
        "DEBUG_TB_INTERCEPT_REDIRECTS": False,
        "REDIS_HOST": 'redis',
        "PAGINATION_LIMIT": 100, #TODO: start using this again
        "PAGINATION_DEFAULT": 100,
        "XML": False, # JSON only

        "JOB_QUEUE_REDIS_DB": 1, # for RQ; note CACHE_REDIS_DB above
        "JOB_QUEUE_DEFAULT_NAME": 'nest_default',
        "JOB_QUEUE_WORKERS": 25,

        "USERFILES_DIR": "/userfiles",
        "DEFAULT_CLOUD": "aws", # TODO KNOW-112 knoweng only? or not even there?
        "AUTHENTICATION_STRATEGY": 'nest_py.core.flask.accounts.authentication.NativeAuthenticationStrategy',
        "JWT_SECRET": "GARBAGESECRET", # TODO reject default in production
        "JWT_ISSUER": "NEST_DEMO_CHANGE_IN_PRODUCTION", # TODO reject default in production
        "JWT_AUDIENCES": ["NEST_DEMO_CHANGE_IN_PRODUCTION"], # TODO reject default in production
        "JWT_LIFESPAN": timedelta(days=365)
    }
    return config

def generate_seed_users(project_env, runlevel):
    if project_env == ProjectEnv.hello_world_instance():
        import nest_py.hello_world.hw_config as hw_config
        project_users = hw_config.generate_project_users(runlevel)
    elif project_env == ProjectEnv.knoweng_instance():
        import nest_py.knoweng.knoweng_config as knoweng_config
        project_users = knoweng_config.generate_project_users(runlevel)
    elif project_env == ProjectEnv.mmbdb_instance():
        import nest_py.omix.omix_config as omix_config
        project_users = omix_config.generate_project_users(runlevel)
    else:
        raise Exception("Unsupported project env: " + str(project_env))
    return project_users
    
def _generate_development_params():
    config = {
        "ENV": 'dev',
        "DEBUG": True,
        "DEBUG_TB_ENABLED": True,
        }
    return config

def _generate_production_params():
    config = {
        "ENV": 'prod',
        "DEBUG": False,
        "DEBUG_TB_ENABLED": False,  # Disable Debug toolbar
        }
    return config

