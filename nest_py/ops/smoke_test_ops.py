"""Implements nest_ops smoke_test subcommand."""

import argparse
from nest_py.ops.ops_logger import log
import nest_py.nest_envs as nest_envs
import nest_py.ops.nest_sites as nest_sites

from nest_py.nest_envs import ProjectEnv
from nest_py.ops.nest_sites import NestSite
import nest_py.hello_world.api_clients.hw_api_clients as hw_api_clients
import nest_py.knoweng.api_clients.knoweng_api_clients as knoweng_api_clients
import nest_py.omix.api_clients.omix_api_clients as omix_api_clients

SMOKE_TEST_CMD_HELP = """Run one or all smoke tests against a nest server.
"""

SMOKE_TEST_CMD_DESCRIPTION = SMOKE_TEST_CMD_HELP + """
"""

def register_subcommand(nest_ops_subparsers):
    """
    Given a toplevel commandline 'subparser' from argparse, registers the
    'smoke_test' command as a subcommand, with all appropriate help messages and
    metadata.
    """
    parser = nest_ops_subparsers.add_parser('smoke_test', \
        help=SMOKE_TEST_CMD_HELP, \
        description=SMOKE_TEST_CMD_DESCRIPTION, \
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

    #super ugly callback mechanism from argparse
    parser.set_defaults(func=_run_smoke_test_cmd)
    return

def _run_smoke_test_cmd(arg_map):
    """
    translates arguments from commandline to calls to python methods. Input is
    the output from argparse.parse_args(), output is an exit code indicating if
    the compilation succeeded.
    """
    project_root_dir = arg_map['project_root_dir']
    project_env_name = arg_map['project']
    project_env = ProjectEnv.from_string(project_env_name)
    target_site_name = arg_map['site']
    target_site = NestSite.from_string(target_site_name)
    exit_code = _run_smoke_test(project_env, target_site)
    return exit_code

def _run_smoke_test(project_env, target_site):
    """
    runs the smoke_test subystem. logs the final result and returns
    a 0/1 exit code based on whether all walkthroughs worked.
    """
    http_client = target_site.build_http_client()
    smoke_res = run_project_scripts(project_env, http_client)
    if smoke_res.did_succeed():
        exit_code = 0
    else:
        exit_code = 1
    rpt = smoke_res.get_full_report()
    log(rpt)
    return exit_code

def run_project_scripts(project_env, http_client):
    """
    runs the smoke test for the current project.
    """
    if project_env == ProjectEnv.hello_world_instance():
        smoke_res = hw_api_clients.run_all_smoke_tests(http_client)
    elif project_env == ProjectEnv.knoweng_instance():
        smoke_res = knoweng_api_clients.run_all_smoke_tests(http_client)
    elif project_env == ProjectEnv.mmbdb_instance():
        smoke_res = omix_api_clients.run_all_smoke_tests(http_client)
    else:
        raise Exception("Project smoke scripts not implemented")
    return smoke_res
