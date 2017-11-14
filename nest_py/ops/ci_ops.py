"""
Commandline support for continous-integration tasks that jenkins will run to
define "the build is broken" or not.  Supplies an argparse 'subparser' for
running compilation commands in a nest_ops docker container.
"""
import argparse
import os
import sys
import traceback

import nest_py.ops.compile_ops as compile_ops
import nest_py.ops.doc_ops as doc_ops
import nest_py.ops.clienttest_ops as clienttest_ops
import nest_py.ops.pytest_ops as pytest_ops
import nest_py.ops.docker_ops as docker_ops
import nest_py.ops.db_ops as db_ops
import nest_py.ops.seed_users_ops as seed_users_ops
import nest_py.ops.smoke_test_ops as smoke_test_ops
from nest_py.ops.ops_logger import log

import nest_py.nest_envs as nest_envs
from nest_py.nest_envs import ProjectEnv, RunLevel
from nest_py.ops.nest_sites import NestSite

VALID_BRANCH_TYPES = ['feature', 'develop', 'master']
DEFAULT_BRANCH_TYPE = 'feature'

#this is the brief comment in the list of subcommands
CI_CMD_HELP = """Run continuous-integration tasks (build, test, deploy)."""

#this is the help message used by 'nest_ops compile --help'
CI_CMD_DESCRIPTION = CI_CMD_HELP + """
"""

BRANCH_TYPE_ARG_HELP = """The type of git branch:
    feature : unmerged feature branches. runs tests.
    develop : mainline development branch. Runs tests then deploys to staging
    master  : mainline stable branch. Run tests then deploy to demo
    """

def register_subcommand(nest_ops_subparsers):
    """
    Given a toplevel commandline 'subparser' from argparse, registers the
    'ci' command as a subcommand, with all appropriate help messages and
    metadata. Sets the callback to '_run_compile_cmd' when the compile
    subcommand is called.
    """
    parser = nest_ops_subparsers.add_parser('ci', \
        help=CI_CMD_HELP, \
        description=CI_CMD_DESCRIPTION, \
        formatter_class=argparse.RawTextHelpFormatter )

    parser.add_argument('branch_type', \
        choices=VALID_BRANCH_TYPES, \
        help=BRANCH_TYPE_ARG_HELP, \
        default=DEFAULT_BRANCH_TYPE \
        )

    #super ugly callback mechanism from argparse
    parser.set_defaults(func=_run_ci_cmd)
    return

def _run_ci_cmd(arg_map):
    """
    translates arguments from commandline to calls
    to python methods. Input is the output from
    argparse.parse_args(), output is an exit code
    indicating if the job succeeded. 
    """
    branch_type = arg_map['branch_type']
    project_root_dir = arg_map['project_root_dir']
    exit_code = _run_ci(branch_type, project_root_dir)
    return exit_code

def _run_ci(branch_type, project_root_dir):
    #currently all the same
    exit_code = build_and_test(project_root_dir)
    return exit_code

def build_and_test(project_root_dir):
    """
    run all compilation and unit tests
    """

    stage_results = list()

    log("START ci_ops.BUILD_AND_TEST")

    py_compile_stage = _perform_stage('python compilation    ', 
        compile_ops._compile, 
        project_root_dir, 
        'python',
        ProjectEnv.default_instance(),
        RunLevel.development_instance())
    stage_results.append(py_compile_stage)


    js_compile_stage = _perform_stage('web_assets compilation', 
        compile_ops._compile, project_root_dir, 'web_assets', 
        ProjectEnv.hello_world_instance(),
        RunLevel.development_instance())
    stage_results.append(js_compile_stage)

    build_containers_stage = _perform_stage('build containers      ', 
        docker_ops._docker_action,
            'build', 'all', 
            ProjectEnv.hello_world_instance() ,
            RunLevel.development_instance() ,
            NestSite.localhost_instance() ,
            project_root_dir)
    stage_results.append(build_containers_stage)

    #run pytests and clienttests against the hello_world_app containers
    startup_containers_stage = _perform_stage('startup containers    ', 
        docker_ops._docker_action,
            'startup', 'all', 
            ProjectEnv.hello_world_instance() ,
            RunLevel.development_instance() ,
            NestSite.localhost_instance() ,
            project_root_dir)
    stage_results.append(startup_containers_stage)

    clienttest_stage = _perform_stage('clienttest            ',
        clienttest_ops._run_unit_test, project_root_dir)
    stage_results.append(clienttest_stage)
    
    pytest_stage = _perform_stage('pytest tests/unit/    ',
        pytest_ops._run_unit_test, project_root_dir, True)
    stage_results.append(pytest_stage)

    teardown_containers_stage = _perform_stage('teardown containers   ', 
        docker_ops._docker_action,
            'teardown', 'all', 
            ProjectEnv.hello_world_instance() ,
            RunLevel.development_instance() ,
            NestSite.localhost_instance() ,
            project_root_dir)
    stage_results.append(teardown_containers_stage)

    #test the lifecycle and smoke scripts of all projects
    project_names = nest_envs.VALID_PROJECT_NAMES
    for project_name in project_names:
        project_env = ProjectEnv(project_name)
        project_stage_results = _perform_project_stages(project_env, project_root_dir)
        stage_results += project_stage_results

    exit_code = _finalize_build(stage_results)
    log("BUILD_AND_TESTS returning exit_code: " + str(exit_code))
    return exit_code

def _perform_project_stages(project_env, project_root_dir):
    """
    performs the stages of an individual project: docker startup,
    seed_users, smoke_tests, docker teardown

    takes a ProjectEnv 
    Returns a list of stage_results (the objects returned
        by _perform_stage)
    """
    stage_results = list()
    project_name = project_env.get_project_name()
    stage_name = project_name + ' web_assets:dist'
    client_dist_stage = _perform_stage(stage_name,
        compile_ops._compile, 
        project_root_dir, 
        'web_assets:dist', 
        ProjectEnv.hello_world_instance(),
        RunLevel.development_instance())
    stage_results.append(client_dist_stage)
    
    stage_name = project_name + ' startup containers'
    startup_containers_stage = _perform_stage(stage_name, 
            docker_ops._docker_action,
            'startup', 'all', 
            project_env,
            RunLevel.development_instance() ,
            NestSite.localhost_instance() ,
            project_root_dir)
    stage_results.append(startup_containers_stage)
 
    stage_name = project_name + ' ensure db tables'
    db_tables_project_stage = _perform_stage(stage_name,
            db_ops._run_db_action,
            'ensure_tables',
            project_env,
            NestSite.localhost_instance())
    stage_results.append(db_tables_project_stage)
    
    stage_name = project_name + ' seed_users'
    seed_users_project_stage = _perform_stage(stage_name,
            seed_users_ops._run_seed_users_script,
            project_env,
            RunLevel.development_instance())
    stage_results.append(seed_users_project_stage)

    stage_name = project_name + ' smoke_test'
    smoke_project_stage = _perform_stage(stage_name,
            smoke_test_ops._run_smoke_test,
            project_env,
            NestSite.localhost_instance())
    stage_results.append(smoke_project_stage)

    stage_name = project_name +  ' teardown containers'
    teardown_containers_stage = _perform_stage(stage_name,
            docker_ops._docker_action,
            'teardown', 'all', 
            project_env,
            RunLevel.development_instance() ,
            NestSite.localhost_instance() ,
            project_root_dir)
    stage_results.append(teardown_containers_stage)

    return stage_results

def _perform_stage(stage_name, stage_fun, *args):
    """
    takes a function that performs a build stage and returns an exit_code
    (where the exit code is 0 on success and >0 otherwise)
    Also takes any arguments that need to be fed into that function.

    Returns a tuple of (success:boolean, stage_name:string, status_msg:string). 

    This provides a common way of doing hardened error checking so that the
    ci job will always finish and print Failure, regardless of how 
    bad the errors are. Also makes consistent reporting.
    """
    log(str(80 * '#'))
    log("CI STAGE BEGIN: " + stage_name)
    try:
        exit_code = stage_fun(*args)
        if exit_code == 0:
            success = True
            status_msg = 'SUCCEEDED'
        else:
            success = False
            status_msg = 'FAILED with exit_code: ' + str(exit_code)
    except Exception as e:
        status_msg = "FAILED with exception: " + str(e)
        success = False
    log("CI STAGE END : " + stage_name + ' :: ' + str(status_msg))
    log(str(80 * '#'))
    ret_pair = (success, stage_name, status_msg)
    return ret_pair

def _finalize_build(stage_results):
    """
    stage_results (list of (stage_exit_code, stage_name, stage_status)) as returned by
        _perform_stage()

    logs a final report and returns an overall exit code for whether the 
    build succeeded.
    """
    overall_success = True
    final_report = ""
    for stage_result in stage_results:
        stage_success, x, y = stage_result
        overall_success = overall_success and stage_success

    final_report += _format_stages_summary(stage_results)

    final_report += '\n'
    if overall_success:
        final_report += "BUILD SUCCEEDED"
        exit_code = 0
    else:
        final_report += "BUILD FAILED"
        exit_code = 1
    log(final_report)
    return exit_code

def _format_stages_summary(stage_results):
    """
    stage_results (list of (tuples of 
        (success:boolean, stage_name:string, status_msg:string)))
    returns a string of a report, one line per stage.
    Something like:
        Stage: <stage x>  :: SUCCESS
        Stage: <stage y>  :: FAILED
        Stage: <stage z>  :: SUCCESS
    """
    #find the longest stage name to pad report lines
    max_name_len = 0
    for entry in stage_results:
        x, stage_name, y = entry
        name_len = len(stage_name)
        if name_len > max_name_len:
            max_name_len = name_len

    summary = ""
    for entry in stage_results:
        x, stage_name, status_msg = entry
        summary += 'Stage: ' + stage_name.ljust(max_name_len) + ":: " 
        summary += status_msg + '\n'
    
    return summary
