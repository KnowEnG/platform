
import os
from datetime import datetime

from nest_py.core.db.sqla_resources import JobsSqlaResources
from nest_py.nest_envs import ProjectEnv, RunLevel
from nest_py.ops.nest_sites import NestSite

def generate_db_config(project_env=None, runlevel=None, site=None):
    if project_env is None:
        project_env = ProjectEnv.hello_world_instance()
    if runlevel is None:
        runlevel = RunLevel.development_instance()
    if site is None:
        site = NestSite.localhost_instance()
    config = {
        "host": os.environ.get("POSTGRES_HOST", site.get_server_ip_address()),
        "user": os.getenv('POSTGRES_USERNAME', "nest"),
        "port": os.getenv('POSTGRES_PORT', 5432), #exported in docker startup
        "password":os.getenv('POSTGRES_PASSWORD', "GARBAGESECRET"),
        "db_name":os.getenv('POSTGRES_DATABASE', "nest"),
        #"verbose_logging":True
        "verbose_logging":False
    }
    return config

#At import time, we default to a plain JobsSqlaResources in order
#to create a declarative_base that the ORM classes can use.
#This is a bit complicated because once the configs are actually
#processed, a job or nest_ops will need to assign database connection
#information to this object. In the case of flask, this object will be
#overwritten completely and this default instance will be ignored
#thereafter and flask_sqlalchemy package  will be responsible for
#binding the ORM classes to the Metadata
GLOBAL_SQLA_RESOURCES = JobsSqlaResources(generate_db_config())

def set_global_sqla_resources(sqla_resources):
    """
    sqla_resources (either JobsSqlaResources or FlaskSqlaResources)
    FIXME this needs more work before it can be used
    see https://visualanalytics.atlassian.net/browse/TOOL-510
    """
    global GLOBAL_SQLA_RESOURCES
    GLOBAL_SQLA_RESOURCES = sqla_resources
    return

def get_global_sqlalchemy_base():
    if GLOBAL_SQLA_RESOURCES is None:
        raise Exception('SQLA resources not initialized')
    base = GLOBAL_SQLA_RESOURCES.get_declarative_base()
    return base

def get_global_sqlalchemy_metadata():
    if GLOBAL_SQLA_RESOURCES is None:
        raise Exception('SQLA resources not initialized')
    md = GLOBAL_SQLA_RESOURCES.get_metadata()
    return md

def get_global_sqlalchemy_session():
    if GLOBAL_SQLA_RESOURCES is None:
        raise Exception('SQLA resources not initialized')
    session = GLOBAL_SQLA_RESOURCES.get_session()
    return session

def get_global_sqlalchemy_engine():
    if GLOBAL_SQLA_RESOURCES is None:
        raise Exception('SQLA resources not initialized')
    engine = GLOBAL_SQLA_RESOURCES.get_engine()
    return engine
