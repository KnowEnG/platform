"""
Implements nest_ops db subcommand, which
does database initializing and clearing and
a few simple info methods
"""

import argparse
from nest_py.ops.ops_logger import log
import nest_py.nest_envs as nest_envs
import nest_py.ops.nest_sites as nest_sites

from nest_py.nest_envs import ProjectEnv
from nest_py.ops.nest_sites import NestSite

import nest_py.core.db.nest_db as nest_db
import nest_py.core.db.db_ops_utils as db_ops_utils

import nest_py.ops.container_users as container_users
from nest_py.ops.command_runner import CommandRunnerLocal
import nest_py.ops.docker_ops as docker_ops

import nest_py.hello_world.db.hw_db as hw_db
import nest_py.omix.db.omix_db as omix_db
import nest_py.knoweng.db.knoweng_db as knoweng_db

DB_CMD_HELP = """Directly manipulate a Postgres database used by Nest.
"""

DB_CMD_DESCRIPTION = DB_CMD_HELP + """
"""

ACTION_ARG_DESCRIPTION = """
check_connection: verify the db is running and accessible
list_tables: list tables that exist in the Postgres DB
ensure_tables: 
drop_tables: 
list_bindings: list tables Nest expects to be in the Postgres DB
psql: open a psql command prompt that accesses the current Postgres DB
"""

VALID_ACTIONS = ['check_connection', 'list_tables', 'ensure_tables', 'drop_tables', 'list_bindings', 'psql']

def register_subcommand(nest_ops_subparsers):
    """
    Given a toplevel commandline 'subparser' from argparse, registers the
    'DB' command as a subcommand, with all appropriate help messages and
    metadata.
    """
    parser = nest_ops_subparsers.add_parser('db', \
        help=DB_CMD_HELP, \
        description=DB_CMD_DESCRIPTION, \
        formatter_class=argparse.RawTextHelpFormatter)

    parser.add_argument('action', \
        help=ACTION_ARG_DESCRIPTION, \
        nargs='?', \
        choices=VALID_ACTIONS, \
        )

    parser.add_argument('--project',
        help='',
        nargs='?',
        choices=nest_envs.VALID_PROJECT_NAMES,
        default=nest_envs.DEFAULT_PROJECT_NAME,
        )

    parser.add_argument('--site',
        help='',
        nargs='?',
        choices=nest_sites.VALID_NEST_SITE_NAMES,
        default=nest_sites.DEFAULT_NEST_SITE_NAME,
        )

    parser.set_defaults(func=_run_db_cmd)
    return

def _run_db_cmd(arg_map):
    """
    translates arguments from commandline to calls to python methods. Input is
    the output from argparse.parse_args(), output is an exit code indicating if
    the job succeeded.
    """
    project_root_dir = arg_map['project_root_dir']
    project_env_name = arg_map['project']
    project_env = ProjectEnv.from_string(project_env_name)
    target_site_name = arg_map['site']
    target_site = NestSite.from_string(target_site_name)
    action = arg_map['action']
    exit_code = _run_db_action(action, project_env, target_site)
    return exit_code

def _run_db_action(action, project_env, target_site):
    """
    runs a db command. logs the final result and returns
    a 0/1 exit code.
    """
    db_config = _construct_config(project_env, target_site) 
    sqla_res = nest_db.GLOBAL_SQLA_RESOURCES
    sqla_res.set_config(db_config)
    sqla_md = sqla_res.get_metadata()
    _bind_tables_to_metadata(sqla_md, project_env)

    succeeded = False
    if 'list_bindings' == action:
        succeeded = db_ops_utils.list_metadata_tables()
    elif 'ensure_tables' == action:
        succeeded = db_ops_utils.ensure_tables_in_db()
    elif 'list_tables' == action:
        succeeded = db_ops_utils.list_tables_in_db()
    elif 'drop_tables' == action:
        succeeded = db_ops_utils.drop_tables_in_db()
    elif 'check_connection' == action:
        succeeded = db_ops_utils.check_db_connection()
    elif 'psql' == action:
        succeeded = open_psql_prompt(project_env, target_site)
    else:
        print('unknown db action: ' + action)
        succeeded = False
    if succeeded:
        exit_code = 0
    else:
        exit_code = 1    
    return exit_code

def open_psql_prompt(project_env, target_site):

    c_user = container_users.make_host_user_container_user()
    runner = CommandRunnerLocal(c_user)
    config = _construct_config(project_env, target_site) 
    cmd = 'docker exec -it postgres_i '
    #cmd += ' /bin/bash'
    db_name = config['db_name']
    #db_name = 'nest_test'
    cmd += '/usr/lib/postgresql/9.6/bin/psql'
    cmd += ' --dbname=' + db_name
    cmd += ' --username=' + config['user']
    cmd += ' --port=' + str(config['port'])
    log(cmd)
    res = runner.run(cmd, stream_log=False, interactive=True)
    return res.get_exit_code()
    
def _construct_config(project_env, target_site):
    proj_config = nest_db.generate_db_config(project_env=project_env)
    return proj_config

def _bind_tables_to_metadata(sqla_metadata, project_env):
    """
    ORMs created using a declarative_base class definition
    will already be registered with the global sqla metadata object,
    but we still need those dynamically produced by the project
    configs.
    TODO: only bind the tables for the current project
    """
    if ProjectEnv.hello_world_instance() == project_env:
        hw_db.register_sqla_bindings(sqla_metadata)
    elif ProjectEnv.mmbdb_instance() == project_env:
        omix_db.register_sqla_bindings(sqla_metadata)
    elif ProjectEnv.knoweng_instance() == project_env:
        knoweng_db.register_sqla_bindings(sqla_metadata)
    return

