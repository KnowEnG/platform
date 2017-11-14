"""
Implements nest_ops seed subcommand, which
does data loading of a canned set of data and analytics
for a project to the nest backend.
"""

import argparse
from nest_py.ops.ops_logger import log
import nest_py.nest_envs as nest_envs
import nest_py.ops.nest_sites as nest_sites

from nest_py.core.api_clients.http_client import NestHttpRequest
from nest_py.nest_envs import ProjectEnv
from nest_py.ops.nest_sites import NestSite
import nest_py.omix.api_clients.omix_api_clients as omix_api_clients
import nest_py.hello_world.api_clients.hw_api_clients as hw_api_clients
import nest_py.knoweng.api_clients.knoweng_api_clients as knoweng_api_clients
import nest_py.core.jobs.jobs_auth as jobs_auth

WIPE_CMD_HELP = """Delete all data from all eve endpoints that store data for a project
"""

WIPE_CMD_DESCRIPTION = WIPE_CMD_HELP + """
"""

def register_subcommand(nest_ops_subparsers):
    """
    Given a toplevel commandline 'subparser' from argparse, registers the
    'seed' command as a subcommand, with all appropriate help messages and
    metadata.
    """
    parser = nest_ops_subparsers.add_parser('wipe', \
        help=WIPE_CMD_HELP, \
        description=WIPE_CMD_DESCRIPTION, \
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

    parser.set_defaults(func=_run_wipe_cmd)
    return

def _run_wipe_cmd(arg_map):
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
    exit_code = _run_wipe(project_env, target_site)
    return exit_code

def _run_wipe(project_env, target_site):
    """
    runs a seeding job. logs the final result and returns
    a 0/1 exit code based on whether all walkthroughs worked.
    """
    http_client = target_site.build_http_client()
    jobs_auth.login_jobs_user(http_client)

    if project_env == ProjectEnv.hello_world_instance():
        cms = hw_api_clients.get_api_client_makers()
    elif project_env == ProjectEnv.knoweng_instance():
        # TODO add option to govern handling of user data
        cms = knoweng_api_clients.get_api_client_makers()
    elif project_env == ProjectEnv.mmbdb_instance():
        cms = omix_api_clients.get_api_client_makers()
    else:
        raise Exception("Project's wipe job not implemented")
    exit_code = wipe_by_api_clients(cms, http_client)
    return exit_code

def wipe_by_api_clients(api_client_makers, http_client):

    """
    api_client_makers(list of ApiClientMaker)
    http_client(NestHttpClient)
    """
    exit_code = 0
    for cm in api_client_makers.values():
        log("wiping collection endpoint: " + cm.get_collection_name())
        api_client = cm.get_crud_client(http_client)
        resp = api_client.response_of_delete_all_entries()
        if resp.did_succeed():
            num_deleted = resp.get_data_payload_as_jdata()['num_deleted']
            log(" .. deleted: " + str(num_deleted))
        else:
            log(" ... FAILED")
            log(resp.get_error_message())
            exit_code = 1
    return exit_code

