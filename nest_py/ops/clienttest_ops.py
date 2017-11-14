import argparse
import os
import traceback
from subprocess import call
import nest_py.ops.docker_ops as docker_ops
from nest_py.ops.ops_logger import log
import nest_py.ops.container_users as container_users

CLIENTTEST_CMD_HELP = """Run all client unit tests.
"""

CLIENTTEST_CMD_DESCRIPTION = CLIENTTEST_CMD_HELP + """
"""

DISPLAY = None

def register_subcommand(nest_ops_subparsers):
    """
    Given a toplevel commandline 'subparser' from argparse, registers the
    'clienttest' command as a subcommand, with all appropriate help messages and
    metadata.
    """
    parser = nest_ops_subparsers.add_parser('clienttest', \
        help=CLIENTTEST_CMD_HELP, \
        description=CLIENTTEST_CMD_DESCRIPTION, \
        formatter_class=argparse.RawTextHelpFormatter )

    #super ugly callback mechanism from argparse
    parser.set_defaults(func=_run_clienttest_cmd)
    return

def _run_clienttest_cmd(arg_map):
    """
    translates arguments from commandline to calls to python methods. Input is
    the output from argparse.parse_args(), output is an exit code indicating if
    the test succeeded.
    """
    project_root_dir = arg_map['project_root_dir']
    exit_code = _run_unit_test(project_root_dir)
    return exit_code
    
def _start_x():
    """
    Starts X server.
    """
    from pyvirtualdisplay import Display
    DISPLAY = Display(visible=0, size=(1024, 768))
    DISPLAY.start()
    
def _stop_x():
    """
    Stops X server.
    """
    if DISPLAY:
        DISPLAY.stop()

def _run_unit_test(project_root_dir):
    """
    Runs all client tests.

    Returns zero if all tests succeed, non-zero otherwise.
    """
    _start_x()
    clientdir = os.path.join(project_root_dir, 'client')
    gulppath = os.path.join(clientdir, 'node_modules', '.bin', 'gulp') 
    cmd = gulppath + ' test'

    cr = container_users.make_host_user_command_runner()
    cr.set_working_dir(clientdir)
    res = cr.run(cmd, stream_log=True)
    exit_code = res.get_exit_code()
    _stop_x()
    return exit_code
