#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
"""

#this should make imports work for all nest_ops subcommands that
#rely on code in other parts of the nest/nest/ package
import argparse
import logging
import os
import sys
import traceback

from nest_py.core.jobs.checkpoint import CheckpointTimer

import nest_py.ops.ci_ops as ci_ops
import nest_py.ops.clienttest_ops as clienttest_ops
import nest_py.ops.compile_ops as compile_ops
import nest_py.ops.db_ops as db_ops
import nest_py.ops.deploy_ops as deploy_ops
import nest_py.ops.doc_ops as doc_ops
import nest_py.ops.docker_ops as docker_ops
import nest_py.ops.pytest_ops as pytest_ops
import nest_py.ops.remote_maintenance_ops as remote_maintenance_ops
import nest_py.ops.seed_ops as seed_ops
import nest_py.ops.seed_users_ops as seed_users_ops
import nest_py.ops.smoke_test_ops as smoke_test_ops
import nest_py.ops.wipe_ops as wipe_ops
import nest_py.ops.wix_ops as wix_ops

logging.basicConfig()

PROFILE = False

CMD_DESCRIPTION = """
Commands that operate against the code, output files to local working directory.
Docker commands build locally then deploy and start/stop on a specified host's
docker daemon.
"""
def main(args_from_commandline):
    parser = argparse.ArgumentParser(prog='nest_ops', \
        description=CMD_DESCRIPTION, \
        formatter_class=argparse.RawTextHelpFormatter)
    subparsers = parser.add_subparsers(title='subcommands', \
        description=None, \
        help=None)
    compile_ops.register_subcommand(subparsers)
    doc_ops.register_subcommand(subparsers)
    clienttest_ops.register_subcommand(subparsers)
    pytest_ops.register_subcommand(subparsers)
    docker_ops.register_subcommand(subparsers)
    smoke_test_ops.register_subcommand(subparsers)
    ci_ops.register_subcommand(subparsers)
    deploy_ops.register_subcommand(subparsers)
    remote_maintenance_ops.register_subcommand(subparsers)
    seed_ops.register_subcommand(subparsers)
    seed_users_ops.register_subcommand(subparsers)
    wipe_ops.register_subcommand(subparsers)
    wix_ops.register_subcommand(subparsers)
    db_ops.register_subcommand(subparsers)
    _register_all_help_subcommand(subparsers)

    #treat zero args the same as asking for --help, but with an error code
    if len(args_from_commandline) == 0:
        parser.print_help()
        sys.exit(1)

    exit_code = _run_subcommand(parser, args_from_commandline)
    return exit_code

def _run_subcommand(main_parser, args_from_commandline):
    """
    returns an exit_code
    """
    args = main_parser.parse_args(args_from_commandline)
    arg_map = vars(args)
    arg_map['project_root_dir'] = detect_project_root_dir()
    arg_map['main_parser'] = main_parser
    try:
        exit_code = args.func(arg_map)
    except Exception as e:
        print('command failed with exception: ' + str(e))
        traceback.print_exc()
        exit_code = 1
    return exit_code

def detect_project_root_dir():
    cmd_dir = os.path.abspath(os.path.dirname(__file__))
    project_dir = os.path.join(cmd_dir, '../../')
    project_dir = os.path.normpath(project_dir)
    return project_dir

def _register_all_help_subcommand(subparsers):
    """
    adds a subcommand 'all_help', that iterates through
    the subcommands and prints their help messages.
    Used to create documentation.
    """
    parser = subparsers.add_parser('all_help', \
        help="Print all subcommands' long-form help messages")
    parser.set_defaults(func=_print_all_help)
    return

def _print_all_help(arg_map):
    exit_code = 1
    main_parser = arg_map['main_parser']
    #there is no good way to retrieve the list of subcommands from the parser
    known_subcommands = ['doc', 'compile', 'clienttest', 'pytest', 'docker', \
        'ci', 'all_help']

    #this is the toplevel help msg of all commands with one-line summaries
    main_parser.print_help()

    for subcommand in known_subcommands:
        sys.stdout.flush()
        print('\n##################')
        print('### ' + subcommand + ' ###')
        print('####################\n')
        try:
            _run_subcommand(main_parser, [subcommand, '--help'])
        except SystemExit:
            #subcommand help likes to call sys.exit() for you. catch
            #it and do nothing
            pass

    exit_code = 0
    return exit_code

def _prof_main():
    start_time = CheckpointTimer.current_time()
    exit_code = main(sys.argv[1:])
    if exit_code == 0:
        status = 'SUCCESS'
    else:
        status = 'FAILURE'

    end_time = CheckpointTimer.current_time()
    elapsed_secs = end_time - start_time
    formatted_secs = CheckpointTimer.format_elapsed_secs(elapsed_secs)

    print('nest_ops exit_code: ' + str(exit_code) + ' (' + status + '). Took: ' + formatted_secs)
    sys.exit(exit_code)

if __name__ == '__main__':
    if PROFILE:
        import cProfile
        import pstats
        cProfile.run("_prof_main()", "{}.profile".format(__file__))
        s = pstats.Stats("{}.profile".format(__file__))
        s.strip_dirs()
        s.sort_stats("time").print_stats(50)
    else:
        _prof_main()
