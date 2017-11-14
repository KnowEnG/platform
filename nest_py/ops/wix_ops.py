"""
Implements 'nest_ops wix' subcommand, which
provides a way to run known nest anayltics jobs from the 
commandline.
"""

import argparse
import os
from nest_py.ops.ops_logger import log

import nest_py.core.jobs.box_downloads as box_downloads
import nest_py.wix.wix_commands as wix_commands

WIX_DATA = 'data/wix/'

WIX_CMD_HELP = """Run a job with a config file that has been
registered in the command registry.
"""

WIX_CMD_DESCRIPTION = WIX_CMD_HELP + """
"""

WIX_COMMAND_HELP = """The name of the wix job to run. Must be from the
list of options.
"""

CONFIG_FILE_HELP = """The name of a file relative to this project's
root directory (normally nest/). If not set, the will be assumed to
be nest/data/wix/<job_key>/<job_key>.cfg

If the default file is not found, a warning will be printed and 
the command will be run with 'None' as the file name
"""

def register_subcommand(nest_ops_subparsers):
    """
    Given a toplevel commandline 'subparser' from argparse, registers the
    'wix' command as a subcommand, with all appropriate help messages and
    metadata.
    """
    parser = nest_ops_subparsers.add_parser('wix', \
        help=WIX_CMD_HELP, \
        description=WIX_CMD_DESCRIPTION, \
        formatter_class=argparse.RawTextHelpFormatter)

    parser.add_argument('wix_command',
        help=WIX_COMMAND_HELP,
        nargs='?',
        choices=wix_commands.valid_job_keys(),
        )

    parser.add_argument('--config-file',
        help=CONFIG_FILE_HELP,
        nargs='?',
        default=None,
        )

    parser.set_defaults(func=_run_wix_cmd)
    return

def _run_wix_cmd(arg_map):
    """
    translates arguments from commandline to calls to python methods. 
    Input is the output from argparse.parse_args(), 
    output is an exit code indicating if the job succeeded.
    """
    job_key = arg_map['wix_command']
    config_file_input = arg_map['config_file']
    project_root_dir = arg_map['project_root_dir']
    wix_data_dir = os.path.join(project_root_dir, WIX_DATA)
    exit_code = wix_commands.run(job_key, config_file_input, wix_data_dir)
    return exit_code


