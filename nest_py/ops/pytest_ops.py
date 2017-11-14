import argparse
import os
import traceback
import nest_py.ops.docker_ops as docker_ops
from nest_py.ops.ops_logger import log
import nest_py.ops.container_users as container_users

PYTEST_CMD_HELP = """Run one or all python unit tests.
"""

PYTEST_CMD_DESCRIPTION = PYTEST_CMD_HELP + """
"""

SPAWN_CONTAINER_ARG_HELP = """
If true, spawn a new docker container with postgres and redis linked 
to run the test(s) in. Requires postgres_i and redis_i to already be 
running. Default is True.
"""

def register_subcommand(nest_ops_subparsers):
    """
    Given a toplevel commandline 'subparser' from argparse, registers the
    'pytest' command as a subcommand, with all appropriate help messages and
    metadata.
    """
    parser = nest_ops_subparsers.add_parser('pytest', \
        help=PYTEST_CMD_HELP, \
        description=PYTEST_CMD_DESCRIPTION, \
        formatter_class=argparse.RawTextHelpFormatter )

    parser.add_argument('python_source_file', \
        help="Name of a python file of unit tests relative to tests/unit/", \
        nargs='?', \
        default=None, \
        )

    parser.add_argument('--spawn-linked-container', \
        help=SPAWN_CONTAINER_ARG_HELP, \
        nargs='?', \
        choices=['true','false','True', 'False'], \
        default='true', \
        )

    #super ugly callback mechanism from argparse
    parser.set_defaults(func=_run_pytest_cmd)
    return

def _run_pytest_cmd(arg_map):
    """
    translates arguments from commandline to calls to python methods. Input is
    the output from argparse.parse_args(), output is an exit code indicating if
    the test succeeded.
    """
    project_root_dir = arg_map['project_root_dir']
    pymodule = arg_map['python_source_file']
    spawn_arg = arg_map['spawn_linked_container'].lower()
    if spawn_arg == 'true':
        spawn_container = True
    elif spawn_arg == 'false':
        spawn_container = False
    else:
        raise Exception("bad arg for spawn_linked_container")
    exit_code = _run_unit_test(project_root_dir, spawn_container, pymodule)
    return exit_code

def _run_unit_test(project_root_dir, spawn_container, python_module=None):
    """
    """
    if spawn_container:
        exit_code = _spawn_and_run_test(project_root_dir, python_module)
    else:
        exit_code = _run_unit_test_local(project_root_dir, python_module)
    return exit_code

def _run_unit_test_local(project_root_dir, python_module=None):
    """
    python_module(string) name of python source code file relative
    to unit_test_dir.
    If python_module is None, runs all tests in unit_test_dir

    Returns zero if all tests succeed, non-zero otherwise.
    """
    import pytest 
    unit_test_dir = os.path.join(project_root_dir, 'nest_py', 'tests', 'unit')
    if python_module is None:
        exit_code = pytest.main([unit_test_dir, '--verbose'])#, '--cov=nest'])
    else:
        test_module_path = os.path.join(unit_test_dir, python_module)
        exit_code = pytest.main([test_module_path, '--verbose'])
    return exit_code

def _spawn_and_run_test(project_root_dir, python_module=None):
    """
    runs the requested test(s) in a copy of the nest_flask container
    with links to postgres and redis containers. 

    the script in docker/run_pytest_in_nest_ops_container.sh does
    the work of starting a new container with the correct links
    based on the nest_flask image. Inside that container, we
    call nest_ops (in a separate process running in that container)
    with the same arguments we received, but with the spawn-linked-container
    set to false so that it runs locally (but locally from inside that
    other container).
    """
    inner_cmd_ary = ["python", "-m", "nest_py.ops.CMD_nest_ops"]
    inner_cmd_ary.extend(["pytest", "--spawn-linked-container=false"])

    if python_module is not None:
        inner_cmd_ary.append(str(python_module))
    #log("bash command to run in spawned container: " + str(inner_cmd_ary))
    docker_dir = os.path.join(project_root_dir, 'docker')
    docker_script = 'run_pytest_in_nest_ops_container.sh'
    exit_code = docker_ops._run_docker_shell_script(docker_script, 
        docker_dir, inner_cmd_ary)
    return exit_code

