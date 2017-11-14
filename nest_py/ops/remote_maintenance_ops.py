"""Implements nest_ops remote_maintenance subcommand."""

import argparse
from nest_py.ops.ops_logger import log
import nest_py.nest_envs as nest_envs
import nest_py.ops.nest_sites as nest_sites

from nest_py.nest_envs import ProjectEnv
from nest_py.ops.nest_sites import NestSite
from nest_py.ops.command_runner import CommandRunnerLocal
from nest_py.ops.command_runner import CommandRunnerRemote
import nest_py.ops.container_users as container_users

CMD_HELP = "Run maintenance script on a remote machine"
CMD_DESCRIPTION= """Runs the command at /home/nestbot/nest_releases/current/ci_scirpts/nightly_maintenance.sh on a remote (target) machine. First shuts down
all docker containers controlled by nest_ops. After running, the
nest app must be redeployed to the target machine.
"""

def register_subcommand(nest_ops_subparsers):
    """
    Given a toplevel commandline 'subparser' from argparse, registers the
    'remote_maintenance' command as a subcommand, with all appropriate 
    help messages and metadata.
    """
    parser = nest_ops_subparsers.add_parser('remote_maintenance', 
        help=CMD_HELP, 
        description=CMD_DESCRIPTION, 
        formatter_class=argparse.RawTextHelpFormatter)

    valid_site_names = list(nest_sites.VALID_NEST_SITE_NAMES)
    valid_site_names.remove('localhost')
    parser.add_argument('--site',
        help='Which remote host in the Nest infrastructure to run the maintenance script on.',
        nargs='?',
        choices=valid_site_names,
        default='staging.hello_world',
        )

    parser.set_defaults(func=_run_remote_maintenance_cmd)
    return

def _run_remote_maintenance_cmd(arg_map):
    """
    translates arguments from commandline to calls to python methods. Input is
    the output from argparse.parse_args(), output is an exit code indicating if
    the maintenance script succeeded.
    """
    target_site_name = arg_map['site']
    target_site = NestSite.from_string(target_site_name)

    if target_site == NestSite.localhost_instance():
        print("Can't perform remote maintenance on localhost. \
            Run ci_scripts/nightly_maintenance.sh directly")
        return 1

    exit_code = _run_remote_maintenance(target_site)
    return exit_code

def _run_remote_maintenance(target_site):
    """
    The local docker containers will run as the current user.

    The remote user will be nestbot.

    """
    local_cmd_runner = container_users.make_host_user_command_runner()
    remote_user = 'nestbot'
    remote_cmd_runner = CommandRunnerRemote(local_cmd_runner,
        target_site, remote_user)
    exit_code = _run_remote_maintenance_commands(remote_cmd_runner)
    return exit_code


def _run_remote_maintenance_commands(command_runner):
    """
    command_runner(CommandRunner): The command_runner should
    be configured to run against the machine and user desired.

    remote_maintenance shuts down the nest app on the remote 
    machine and runs the script at ci_scripts/nightly_maintenance.sh

    This command will run in the directory called ~/nest_releases/current,
    which must already exist and have a valid deployment installed.
    """
    cr = command_runner
    
    try:
        _run_step(cr, 'whoami')

        current_deploy_dir = '~/nest_releases/current/'
        cr.set_remote_working_dir(current_deploy_dir)
        _run_step(cr,'./nest_ops docker teardown --service=all')
        #this seems to always 'fail' if it can't delete 100% of the docker cache,
        #but it is still reclaiming the vast majority of the disk space used
        #by docker, so don't require it to succeed
        _run_step(cr,'sh ./ci_scripts/nightly_maintenance.sh', must_succeed=False)
        exit_code = 0
    except Exception as e:
        log("remote_maintenance Failed")
        log(str(e))
        exit_code = 1

    return exit_code

def _run_step(command_runner, remote_command, must_succeed=True):
    res = command_runner.run(remote_command)
    if must_succeed and not res.succeeded():
        raise Exception("Failed remote_maintenance Step: " + str(res))
    else:
        log(str(res))
    return



