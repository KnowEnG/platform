"""
Implements nest_ops seed subcommand, which
does data loading of a canned set of data and analytics
for a project to the nest backend.
"""

import argparse
from nest_py.ops.ops_logger import log
import nest_py.nest_envs as nest_envs
import nest_py.ops.nest_sites as nest_sites

from nest_py.nest_envs import ProjectEnv
from nest_py.ops.nest_sites import NestSite

import nest_py.hello_world.jobs.hello_world_seed_job as hello_world_seed_job
import nest_py.omix.jobs.mmbdb_seed_job as mmbdb_seed_job
import nest_py.omix.jobs.seed_data as mmbdb_seed_data
import nest_py.knoweng.jobs.knoweng_seed_job as knoweng_seed_job
import nest_py.core.db.nest_db as nest_db

SEED_CMD_HELP = """Run a project's seeding script against a nest server.
"""

SEED_CMD_DESCRIPTION = SEED_CMD_HELP + """
"""

SUBSAMPLE_HELP = """If true, the seed job will subsample any raw data \
it can to make the job run faster but with less precision. default=false"""

def register_subcommand(nest_ops_subparsers):
    """
    Given a toplevel commandline 'subparser' from argparse, registers the
    'seed' command as a subcommand, with all appropriate help messages and
    metadata.
    """
    parser = nest_ops_subparsers.add_parser('seed', \
        help=SEED_CMD_HELP, \
        description=SEED_CMD_DESCRIPTION, \
        formatter_class=argparse.RawTextHelpFormatter)

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

    parser.add_argument('--flavor',
        help='Which data and config to use. Only supported for mmbdb project.',
        nargs='?',
        choices=mmbdb_seed_data.VALID_SEED_FLAVORS,
        default=mmbdb_seed_data.DEFAULT_SEED_FLAVOR
        )


    #NOTE: usage is '--subsample=true', not '--subsample'
    #to make it easier to wrap explicitly in ci scripts
    parser.add_argument('--subsample',
        help=SUBSAMPLE_HELP,
        nargs='?',
        choices=['true', 'false', 'True', 'False'],
        default='false',
        )

    parser.set_defaults(func=_run_seed_cmd)
    return

def _run_seed_cmd(arg_map):
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
    flavor_name = arg_map['flavor']
    subsample_raw = arg_map['subsample']
    subsample_lower = subsample_raw.lower()
    if subsample_lower == 'true':
        subsample = True
    else:
        subsample = False
    exit_code = _run_seed_script(project_env, target_site, flavor_name, subsample)
    return exit_code

def _run_seed_script(project_env, target_site, flavor_name, subsample):
    """
    runs a seeding job. logs the final result and returns
    a 0/1 exit code based on whether all walkthroughs worked.
    """
    http_client = target_site.build_http_client()
    
    data_projects_dir = '/code_live/data/projects/'

    db_engine = _make_db_engine(project_env, target_site)
    if project_env == ProjectEnv.hello_world_instance():
        data_dir = data_projects_dir + 'hello_world/'
        exit_code = hello_world_seed_job.run(http_client, data_dir)
    elif project_env == ProjectEnv.knoweng_instance():
        data_dir = data_projects_dir + 'knoweng/'
        exit_code = knoweng_seed_job.run(http_client, db_engine, data_dir, subsample, flavor_name)
    elif project_env == ProjectEnv.mmbdb_instance():
        data_dir = data_projects_dir + 'mmbdb/'
        exit_code = mmbdb_seed_job.run(http_client, db_engine, data_dir, subsample, flavor_name)
        pass
    else:
        raise Exception("Project's seed job not implemented")
    return exit_code

def _make_db_engine(project_env, site):
    """
    project_env(ProjectEnv): used to determine what tables are expected
    site(NestSite):machine running the database to write results to
    """
    db_config = nest_db.generate_db_config(project_env=project_env, site=site)
    db_config['verbose_logging'] = False

    sqla_res = nest_db.GLOBAL_SQLA_RESOURCES
    sqla_res.set_config(db_config)
    # see https://visualanalytics.atlassian.net/browse/TOOL-510
    # nest_db.set_global_sqla_resources(sqla_res)
    db_engine = nest_db.get_global_sqlalchemy_engine().connect()
    return db_engine
