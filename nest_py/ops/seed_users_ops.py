"""
Implements nest_ops seed subcommand, which
does data loading of a canned set of data and analytics
for a project to the nest backend.
"""

import argparse
from nest_py.ops.ops_logger import log
import nest_py.nest_envs as nest_envs

from nest_py.nest_envs import ProjectEnv
from nest_py.nest_envs import RunLevel

import nest_py.core.db.nest_db as nest_db
import nest_py.ops.nest_sites as nest_sites
from nest_py.ops.nest_sites import NestSite
import nest_py.core.db.db_ops_utils as db_ops_utils

SEED_USERS_CMD_HELP = """Seed the local database with a \
project's pre-configured users."""

SEED_USERS_CMD_DESCRIPTION = SEED_USERS_CMD_HELP + """
"""


def register_subcommand(nest_ops_subparsers):
    """
    Given a toplevel commandline 'subparser' from argparse, registers the
    'seed' command as a subcommand, with all appropriate help messages and
    metadata.
    """
    parser = nest_ops_subparsers.add_parser('seed_users', \
        help=SEED_USERS_CMD_HELP, \
        description=SEED_USERS_CMD_DESCRIPTION, \
        formatter_class=argparse.RawTextHelpFormatter)

    parser.add_argument('--project',
        help='',
        nargs='?',
        choices=nest_envs.VALID_PROJECT_NAMES,
        default=nest_envs.DEFAULT_PROJECT_NAME,
        )

    parser.add_argument('--runlevel', \
        help='Projects can optionally have different users for different runlevels (e.g. to have additional test users in dev mode)',
        choices=nest_envs.VALID_RUNLEVEL_NAMES,
        default=nest_envs.DEFAULT_RUNLEVEL_NAME, \
        )

    parser.add_argument('--site',
        help='',
        nargs='?',
        choices=nest_sites.VALID_NEST_SITE_NAMES,
        default=nest_sites.DEFAULT_NEST_SITE_NAME,
        )

    parser.set_defaults(func=_run_seed_users_cmd)
    return

def _run_seed_users_cmd(arg_map):
    """
    translates arguments from commandline to calls to python methods. Input is
    the output from argparse.parse_args(), output is an exit code indicating if
    the job succeeded.
    """
    project_root_dir = arg_map['project_root_dir']
    project_env_name = arg_map['project']
    project_env = ProjectEnv.from_string(project_env_name)
    runlevel_name = arg_map['runlevel']
    runlevel = RunLevel.from_string(runlevel_name)
    target_site_name = arg_map['site']
    target_site = NestSite.from_string(target_site_name)
    exit_code = _run_seed_users_script(project_env, runlevel, target_site)
    return exit_code

def _run_seed_users_script(project_env, runlevel, target_site):
    """
    """
    _init_db_engine(project_env, target_site)
    try:
        db_ops_utils.seed_users(project_env, runlevel)
        exit_code = 0
    except Exception as e:
        log('ERROR: ' + str(e))
        exit_code = 1
    return exit_code

def _init_db_engine(project_env, target_site):
    db_config = nest_db.generate_db_config(project_env=project_env, site=target_site)
    db_config['verbose_logging'] = False
    sqla_res = nest_db.GLOBAL_SQLA_RESOURCES
    sqla_res.set_config(db_config)
    # see https://visualanalytics.atlassian.net/browse/TOOL-510
    # nest_db.set_global_sqla_resources(sqla_res)
    db_engine = nest_db.get_global_sqlalchemy_engine().connect()
    return
