"""Implements nest_ops deploy subcommand."""

import argparse
from nest_py.ops.ops_logger import log
import nest_py.nest_envs as nest_envs
import nest_py.ops.nest_sites as nest_sites

from nest_py.nest_envs import ProjectEnv
from nest_py.ops.nest_sites import NestSite
from nest_py.ops.command_runner import CommandRunnerLocal
from nest_py.ops.command_runner import CommandRunnerRemote
import nest_py.ops.container_users as container_users

DEPLOY_CMD_HELP = "Download and run the nest stack on a remote machine"
DEPLOY_CMD_DESCRIPTION= """Deploy a particular git version to a remote
nest site. The remote machine must have a user 'nestbot' with a
deploy key installed on bitbucket, and the current user running nest_ops
must have an authorized key to log into the nestbot account.

This command will create or overwrite a directory called
~/nest_releases/nest_<git_branch_or_tag> on the remote machine. The 
requested code will be downloaded from Bitbucket, and the Nest docker
stack will be built and started with a specified active project.
"""

def register_subcommand(nest_ops_subparsers):
    """
    Given a toplevel commandline 'subparser' from argparse, registers the
    'deploy' command as a subcommand, with all appropriate help messages and
    metadata.
    """
    parser = nest_ops_subparsers.add_parser('deploy', \
        help=DEPLOY_CMD_HELP, \
        description=DEPLOY_CMD_DESCRIPTION, \
        formatter_class=argparse.RawTextHelpFormatter)

    parser.add_argument('--project',
        help='What flavor of a Nest server to install on the remote machine',
        nargs='?',
        choices=nest_envs.VALID_PROJECT_NAMES,
        default=nest_envs.DEFAULT_PROJECT_NAME,
        )

    parser.add_argument('--site',
        help='Which remote host in the Nest infrastructure to install to.',
        nargs='?',
        choices=nest_sites.VALID_NEST_SITE_NAMES,
        default=nest_sites.DEFAULT_NEST_SITE_NAME,
        )

    parser.add_argument('--git_tag_or_branch',
        help='An existing tag or branch in the nest repo on Bitbucket. Also works with SHAs.',
        nargs='?',
        default='develop',
        )

    parser.set_defaults(func=_run_deploy_cmd)
    return

def _run_deploy_cmd(arg_map):
    """
    translates arguments from commandline to calls to python methods. Input is
    the output from argparse.parse_args(), output is an exit code indicating if
    the compilation succeeded.
    """
    project_root_dir = arg_map['project_root_dir']
    project_env_name = arg_map['project']
    project_env = ProjectEnv.from_string(project_env_name)
    git_tag_or_branch = arg_map['git_tag_or_branch']
    target_site_name = arg_map['site']
    target_site = NestSite.from_string(target_site_name)
    exit_code = _run_deploy(project_env, git_tag_or_branch, target_site)
    return exit_code

def _run_deploy(project_env, git_tag_or_branch, target_site):
    """
    deploy the given git version on the local machine with the
    given project_env.

    The code will be in the current user's (who is running nest_ops)
    home directory (~/nest_releases/nest_<branch_name>/).

    The docker containers will run as the current user.
    """
    local_cmd_runner = container_users.make_host_user_command_runner()
    remote_user = 'nestbot'
    remote_cmd_runner = CommandRunnerRemote(local_cmd_runner,
        target_site, remote_user)
    exit_code = _run_deploy_commands(project_env, git_tag_or_branch, 
        remote_cmd_runner)
    return exit_code


def _run_deploy_commands(project_env, git_tag_or_branch, command_runner):
    """
    command_runner(CommandRunner): The command_runner should
    be configured to run against the machine and user desired.

    deploys the code of project project_env, at git revision
    git_tag_or_branch, using the given command_runner to run
    the individual bash commands.     

    This command will create a directory called
    ~/nest_releases/nest_<git_sha>/ and launch the
    requested projected from there.
    """
    cr = command_runner
    
    try:
        _run_step(cr, 'whoami')

        # the -p means it won't error if it's already there
        _run_step(cr,'mkdir -p ~/nest_releases')

        #TODO: maintaining these data directories through .gitkeep is starting to
        #get creaky. this is to ensure they exist in a 'shared' space
        #which will live across releases
        shared_data_dir = '~/nest_releases/persistent_data/'

        _run_step(cr,'mkdir -p ' + shared_data_dir + 'userfiles')
        _run_step(cr,'mkdir -p ' + shared_data_dir + 'db')
        _run_step(cr,'mkdir -p ' + shared_data_dir + 'knoweng')

        install_dir = '~/nest_releases/nest_' + git_tag_or_branch
        path_to_current_dir = '~/nest_releases/current'
        project_name = project_env.get_project_name()

        #always delete the install_dir if it exists. it means
        #we're redeploying something that was deployed before
        _run_step(cr,'rm -rf ' + install_dir)

        repo = 'git@bitbucket.org:arivisualanalytics/nest.git'
        _run_step(cr,'git clone -b ' + git_tag_or_branch +
            ' --single-branch ' + repo + ' ' + install_dir)
 
        #replace the soft link to ~/nest_releases/current with a link to what we
        #just installed
        _run_step(cr, 'rm ' + path_to_current_dir, must_succeed=False)
        _run_step(cr, 'ln -s ' + install_dir + ' ' + path_to_current_dir)

        #replace the data/ dir with a link to persistent_data/ 
        cr.set_remote_working_dir(install_dir)
        _run_step(cr,'rm -rf data && ln -s ' + shared_data_dir + ' data')

        #now do standard build and launch

        docker_dir = install_dir + '/docker/'
        cr.set_remote_working_dir(docker_dir)
        _run_step(cr,'sh build_nest_ops.sh')

        cr.set_remote_working_dir(install_dir)
        _run_step(cr,'./nest_ops compile --project=' +
            project_name)

        _run_step(cr,'./nest_ops docker build --service=all --project=' + 
            project_name)
        
        #stop the previous installation if it's running
        _run_step(cr,'./nest_ops docker teardown --service=all')

        _run_step(cr,'./nest_ops docker startup --service=all --project=' +
            project_name)
        
        _run_step(cr,'./nest_ops db ensure_tables --project=' +
            project_name)

        _run_step(cr,'./nest_ops seed_users --project=' +
            project_name)

        #Instruct the target machine to run it's smoke tests against itself.
        #Do it this way in case we are deploying code with different smoke tests
        _run_step(cr,'./nest_ops smoke_test --site=localhost --project=' +
            project_name)

        exit_code = 0
    except Exception as e:
        log("Deploy Failed")
        log(str(e))
        exit_code = 1

    return exit_code


def _run_step(command_runner, remote_command, must_succeed=True):
    res = command_runner.run(remote_command)
    if must_succeed and not res.succeeded():
        raise Exception("Failed Deploy Step: " + str(res))
    else:
        log(str(res))
    return



