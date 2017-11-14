import argparse
import os
import traceback
from subprocess import call

DOC_CMD_HELP = """Generate all docs and api-docs (python, typescript, etc).
"""

DOC_CMD_DESCRIPTION = DOC_CMD_HELP + """
Has no arguments. Will attempt to generate all types of docs
even if one fails.
"""

def register_subcommand(nest_ops_subparsers):
    """
    Given a toplevel commandline 'subparser' from argparse, registers the
    'doc' command as a subcommand, with all appropriate help messages and
    metadata.
    """
    parser = nest_ops_subparsers.add_parser('doc', \
        help=DOC_CMD_HELP, \
        description=DOC_CMD_DESCRIPTION, \
        formatter_class=argparse.RawTextHelpFormatter )

    #super ugly callback mechanism from argparse
    parser.set_defaults(func=_run_doc_cmd)
    return

def _run_doc_cmd(arg_map):
    """
    translates arguments from commandline to calls to python methods. Input is
    the output from argparse.parse_args(), output is an exit code indicating if
    the compilation succeeded.  
    """
    project_root_dir = arg_map['project_root_dir']
    exit_code = _generate_docs(project_root_dir)
    return exit_code

def _generate_docs(project_root_dir):
    """
    Generate the docs and puts them in <project_root_dir>/docs.
    Returns zero if all generator commands succeed, non-zero otherwise.
    """
    from shutil import rmtree
    from sphinx.apidoc import main as sa_main
    from sphinx import main as sb_main
    workdir = os.path.join(project_root_dir, 'docs', 'generated')
    builddir = os.path.join(workdir, '_build')
    doctreesdir = os.path.join(builddir, 'doctrees')
    htmldir = os.path.join(builddir, 'html')
    if os.path.isdir(builddir):
        rmtree(builddir)
    try: 
        sa_main(['sphinx-apidoc', '-F', '-o', workdir, 'nest'])
        sb_main( ['sphinx-build', '-b', 'html', '-d', doctreesdir, workdir, htmldir])
        exit_code = 0
    except Exception:
        exit_code = 1
    return exit_code

