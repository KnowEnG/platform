"""Implements nest_ops docker subcommand."""
import argparse
import os
import time

from nest_py.core.api_clients.http_client import NestHttpRequest
import nest_py.core.db.db_ops_utils as db_ops_utils
from nest_py.nest_envs import ProjectEnv, RunLevel
from nest_py.ops.nest_sites import NestSite
import nest_py.nest_envs as nest_envs
import nest_py.ops.nest_sites as nest_sites
from nest_py.ops.ops_logger import log
import nest_py.ops.container_users as container_users

DOCKER_CMD_HELP = """ Build, Start, Stop docker containers in the nest stack.
"""

DOCKER_CMD_DESCRIPTION = DOCKER_CMD_HELP + """
"""

ACTION_ARG_DESCRIPTION = """
build:    runs 'docker build' on the Dockerfile associated with
           the service. All services must therefore have a Dockerfile
           in nest/docker/, even if they don't add anything to a
           publicly available image. After build, an image is available
           to run on localhost.
startup:  starts the docker container and runs its main executable
teardown: Stops the container and removes it from the list of
           inactive containers. You must remove the previously running
           container before starting a new one as they will try to
           use the same name. Note that this means all containers
           should be considered stateless, and must write any data
           that must survive startup/teardown to a docker 'volume'
           that maps to a file directory on the host machine.
"""

#note that this also defines the order that the containers are started
#when 'startup --service=all' is requested
VALID_DOCKER_SERVICES = ['all', 'postgres', 'redis', 'nest_flask', 'nest_jobs']
DEFAULT_DOCKER_SERVICE = 'all'

VALID_ACTIONS = ['build', 'startup', 'teardown']

def register_subcommand(nest_ops_subparsers):
    """
    Given a toplevel commandline 'subparser' from argparse, registers the
    'docker' command as a subcommand, with all appropriate help messages and
    metadata.
    """
    parser = nest_ops_subparsers.add_parser('docker', \
        help=DOCKER_CMD_HELP, \
        description=DOCKER_CMD_DESCRIPTION, \
        formatter_class=argparse.RawTextHelpFormatter)

    parser.add_argument('action', \
        help=ACTION_ARG_DESCRIPTION, \
        nargs=1, \
        choices=VALID_ACTIONS, \
        )

    parser.add_argument('--project', \
        help="""Which project to run the service as. Note that
            not all commands and services necessarily do anything
            unique for a project-env. Redis ignores it. The nest_flask
            and nest_jobs containers currently ignore it during build
            but then use it during \'start\' so that they expose only
            the correct endpoints, etc. """, \
        choices=nest_envs.VALID_PROJECT_NAMES, \
        default=nest_envs.DEFAULT_PROJECT_NAME, \
        )

    parser.add_argument('--site', \
        help="""The environment of services that is being manipulated,
            either localhost or one of the known shared environments""",
        choices=nest_sites.VALID_NEST_SITE_NAMES,
        default=nest_sites.DEFAULT_NEST_SITE_NAME, \
        )

    parser.add_argument('--runlevel', \
        help='Determines the run level for logging, error checking, etc.',
        choices=nest_envs.VALID_RUNLEVEL_NAMES,
        default=nest_envs.DEFAULT_RUNLEVEL_NAME, \
        )

    parser.add_argument('--service', \
        help='Which of the docker containers within the stack to manipulate.', \
        choices=VALID_DOCKER_SERVICES, \
        default=DEFAULT_DOCKER_SERVICE, \
        )

    #super ugly callback mechanism from argparse
    parser.set_defaults(func=_run_docker_cmd)
    return

def _run_docker_cmd(arg_map):
    """
    translates arguments from commandline to calls to python methods. Input is
    the output from argparse.parse_args(), output is an exit code indicating if
    the compilation succeeded.
    """
    project_root_dir = arg_map['project_root_dir']
    #nargs=1 forces our subcommand into a list of size 1
    action = arg_map['action'][0]
    project_env_name = arg_map['project']
    project_env = ProjectEnv.from_string(project_env_name)
    target_site_name = arg_map['site']
    target_site = NestSite.from_string(target_site_name)
    runlevel_name = arg_map['runlevel']
    runlevel = RunLevel.from_string(runlevel_name)
    service = arg_map['service']
    exit_code = _docker_action(action, service, project_env, \
        runlevel, target_site, project_root_dir)
    return exit_code

def _docker_action(action, service, project_env, runlevel, \
    nest_site, project_root_dir):
    """
    action (String)
    service (String)
    project_env (ProjectEnv)
    runlevel (RunLevel)
    nest_site (NestSite)
    docker_dir (String)
    """
    docker_dir = os.path.join(project_root_dir, 'docker')
    log('Performing Docker action:')
    log('  action=' + str(action))
    log('  service=' + str(service))
    log('  ' + str(project_env))
    log('  ' + str(runlevel))
    log('  ' + str(nest_site))
    log('  ' + str(docker_dir))

    if 'all' == service:
        service_names = list(VALID_DOCKER_SERVICES)
        service_names.remove('all')
    else:
        service_names = [service]

    if 'build' == action:
        exit_code = _docker_build(service_names, project_env, runlevel, \
            docker_dir)
    elif 'startup' == action:
        # we could check status inside _docker_startup, but for the case where
        # we're starting multiple services, it saves us a little time to call
        # start on them all first, then go back and check their statuses
        exit_code = _docker_startup(service_names, project_env, runlevel, \
            nest_site, docker_dir, project_root_dir)
        exit_code += _docker_check_startup(service_names, nest_site)
    elif 'teardown' == action:
        exit_code = _docker_teardown(service_names, project_env, runlevel, \
            nest_site, docker_dir)
    else:
        log("Unknown docker action: '" + str(action) + "'")
        exit_code = 1
    return exit_code

def _make_env_vars(runlevel):
    """
    makes standard env vars to pass to the scripts when they are run. the script
    must be expecting them have a "--env=XXX=xxx" entry for each
    """
    env_vars = dict()
    env_vars['NEST_RUNLEVEL'] = runlevel.get_runlevel_name()
    return env_vars

def _docker_build(service_names, project_env, runlevel, docker_dir):
    """
    """
    exit_sum = 0
    #filter this super verbose message
    trailing_args = ["|grep -v \"Sending build context to Docker daemon\""]
    for service_name in service_names:
        script = _docker_build_script(service_name)
        exit_sum += _run_docker_shell_script(script, docker_dir, trailing_args)
    return exit_sum

def _docker_startup(service_names, project_env, runlevel, nest_site, docker_dir, project_dir):
    """
    """
    exit_sum = 0
    for service_name in service_names:
        script = _docker_startup_script(service_name, project_env)
        trailing_args = None
        env_vars = _make_env_vars(runlevel)
        exit_sum += _run_docker_shell_script(script, docker_dir, trailing_args=trailing_args, env_variables=env_vars)
    return exit_sum

def _docker_check_startup(service_names, nest_site, timeout_secs=180):
    """
    Confirms the services in service_names are running.

    Arguments:
        service_names (list): List of names of services to check.
        nest_site (string): The deployment site name.
        timeout_secs (float): The maximum time in seconds to wait; actual wait
            time may slightly exceed timeout_secs.

    Returns:
        int: the number of services whose statuses are failure or still unknown
            after the timeout expires
    """
    exit_sum = 0

    # to_check contains the names of services whose statuses we haven't yet
    # determined; we'll poll them, removing items as each is determined, until
    # the list is empty or we reach the timeout
    to_check = list(service_names)
    start_time = time.time()

    # fyi, some ways we can exceed timeout_secs:
    # - while condition checks remaining time, which might be < 1s, but sleep
    #       always sleeps 1s
    # - sleep may take longer than requested
    # - checks on individual services may take significant time, especially if
    #   they have their own timeout/retry behavior

    def elapsed_time():
        """Returns time elapsed since start_time, measured in seconds."""
        return time.time() - start_time

    while len(to_check) > 0 and (elapsed_time() < timeout_secs):
        time.sleep(1) # seconds
        # iterating over dict of service/status pairs makes it easy to log
        # changes and remove from to_check
        statuses = {service: _docker_check_status(\
                service, nest_site, timeout_secs - elapsed_time()) \
                for service in to_check}
        current_time = time.ctime()
        for service, status in statuses.iteritems():
            if status == 'success':
                log(service + " ready at " + current_time + \
                        " (" + str(elapsed_time()) + " sec)")
                to_check.remove(service)
            elif status == 'failure':
                log(service + " failed at " + current_time)
                exit_sum += 1
                to_check.remove(service)
            elif status == 'unknown':
                pass
            else:
                raise ValueError("Bad status " + status + " for " + service)

    if len(to_check) > 0:
        log("Timeout expired at " + time.ctime() + \
            " before startup tests complete: " + str(to_check))
        exit_sum += len(to_check)
    return exit_sum

def _docker_check_status(service_name, nest_site, timeout_secs):
    """
    Returns the status of a single service.

    Arguments:
        service_name (string): The name of the service to check; valid values
            are those found in VALID_DOCKER_SERVICES except 'all'.
        nest_site (string): The deployment site name.
        timeout_secs (float): The maximum time in seconds to wait; actual wait
            time may slightly exceed timeout_secs.

    Returns:
        string: one of ['success', 'failure', 'unknown']
    """
    return_val = 'unknown'
    if timeout_secs > 0:
        if service_name in ['redis', 'nest_jobs']:
            # TODO: TOOL-123 implement checks for redis,  and nest_jobs
            return_val = 'success'

        elif service_name == 'postgres':
            succeeded = db_ops_utils.check_db_connection()
            if succeeded:
                return_val = 'success'
            else:
                return_val = 'unknown'
        elif service_name == 'nest_flask':
            # check the top-level Eve endpoint
            # this not only tells us Eve is running, it also forces wsgi to
            # initialize the app and (at least for modjy) warms up the code
            # cache
            http_client = nest_site.build_http_client()
            # using '' as relative URL for top-level endpoint; '/api' is
            # implicit
            request = NestHttpRequest(
                    'heartbeat', num_tries=1, timeout_secs=timeout_secs)
            response = http_client.perform_request(request)
            if response.did_succeed():
                return_val = 'success'
        else:
            raise ValueError("Bad service " + service_name)
    return return_val

def _docker_teardown(service_names, project_env, runlevel, nest_site, docker_dir):
    """
    """
    exit_sum = 0
    for service_name in service_names:
        script = _docker_teardown_script(service_name)
        exit_sum += _run_docker_shell_script(script, docker_dir)
    #the exit sum will be greater than zero if the containers were already gone.
    no_error = 0
    return no_error

def _docker_build_script(service):
    script_base = 'build_' + service + '.sh'
    return script_base

def _docker_startup_script(service, project_env):
    if service in ['nest_flask', 'nest_jobs']:
        script_base = 'start_' + project_env.get_project_name()
        script_base += '_' + str(service) + '_container.sh'
    else:
        script_base = 'start_' + str(service) + '_container.sh'
    return script_base

def _docker_teardown_script(service):
    script_base = 'stop_' + str(service) + '_container.sh'
    return script_base

def _run_docker_shell_script(script_name, docker_dir, trailing_args=None,
    env_variables=dict()):
    """
    script_name (String) filename of a script in the nest/docker/ directory
    docker_dir (String) directory of docker scripts in the nest repo. expected
        to be /code_live/docker, but may be different is run outside
        of the nest_ops container
    env_variables (dict of string->string): will be set as commandline env
        variables in the shell that the script is run

    """
    #sh cannot be broken into its own list element or you will be dropped
    #into a shell
    cmd_ary = [('sh ' + script_name)]
    if trailing_args is not None:
        cmd_ary.extend(trailing_args)
    cmd = " ".join(cmd_ary)
    log("Executing command: " + str(cmd))
    cr = container_users.make_host_user_command_runner()
    cr.set_working_dir(docker_dir)
    cr.add_env_variables(env_variables)
    result = cr.run(cmd, stream_log=True)
    exit_code = result.get_exit_code()
    return exit_code
