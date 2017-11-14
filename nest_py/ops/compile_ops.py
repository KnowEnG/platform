"""
Commandline support for compilation tasks. Supplies an
argparse 'subparser' for running compilation commands
in a nest_ops docker container.
"""
import argparse
import os
import traceback
from shutil import rmtree
from nest_py.ops.ops_logger import log
import nest_py.ops.container_users as container_users
import nest_py.knoweng.knoweng_config as knoweng_config
import nest_py.nest_envs as nest_envs
from nest_py.nest_envs import ProjectEnv,RunLevel

VALID_CODE_TYPES = ['python', 'web_assets', 'web_assets:npm', 'web_assets:ts',
    'web_assets:dist', 'all']

#this is the brief comment in the list of subcommands
COMPILE_CMD_HELP = """Compile a type of code, or everything."""

#this is the help message used by 'nest_ops compile --help'
COMPILE_CMD_DESCRIPTION = COMPILE_CMD_HELP + """
"""

CODE_TYPE_ARG_HELP = """The target code type to compile
    python         : runs pylint with 'errors' only reporting
    web_assets     : runs web_assets:npm, web_assets:ts, and web_assets:dist
    web_assets:npm : (re)installs node packages
    web_assets:ts  : compiles typescript, builds all assets
    web_assets:dist: prepares the client/dist directory to serve the specified project's assets
    all            : (default) all of the above"""

def register_subcommand(nest_ops_subparsers):
    """
    Given a toplevel commandline 'subparser' from argparse, registers the
    'compile' command as a subcommand, with all appropriate help messages and
    metadata. Sets the callback to '_run_compile_cmd' when the compile
    subcommand is called.
    """
    parser = nest_ops_subparsers.add_parser('compile', \
        help=COMPILE_CMD_HELP, \
        description=COMPILE_CMD_DESCRIPTION, \
        formatter_class=argparse.RawTextHelpFormatter )

    parser.add_argument('--code_type', \
        choices=VALID_CODE_TYPES, \
        help=CODE_TYPE_ARG_HELP, \
        default='all' \
        )

    parser.add_argument('--project', \
        help="""Which project to build. Only affects the web_assets:dist
            code_type, where it determines which project's index.html
            will be the main entry point index.html in the static files.""", \
        choices=nest_envs.VALID_PROJECT_NAMES, \
        default=nest_envs.DEFAULT_PROJECT_NAME, \
        )
        
    parser.add_argument('--runlevel', \
        help='Determines the run level for logging, error checking, etc.',
        choices=nest_envs.VALID_RUNLEVEL_NAMES,
        default=nest_envs.DEFAULT_RUNLEVEL_NAME, \
        )

    #super ugly callback mechanism from argparse
    parser.set_defaults(func=_run_compile_cmd)
    return

def _run_compile_cmd(arg_map):
    """
    translates arguments from commandline to calls
    to python methods. Input is the output from
    argparse.parse_args(), output is an exit code
    indicating if the compilation succeeded. 
    """
    code_type = arg_map['code_type']
    project_root_dir = arg_map['project_root_dir']
    project_env_name = arg_map['project']
    runlevel_name = arg_map['runlevel']
    project_env = ProjectEnv.from_string(project_env_name)
    runlevel = RunLevel.from_string(runlevel_name)
    exit_code = _compile(project_root_dir, code_type, project_env, runlevel)
    return exit_code

def _compile(project_root_dir, code_type, project_env, runlevel):
    if 'python' == code_type:
        exit_code = _compile_python(project_root_dir)
    elif 'web_assets' == code_type:
        exit_code = _compile_web_assets(project_env, project_root_dir, runlevel)
    elif 'web_assets:npm' == code_type:
        exit_code = _compile_web_assets_npm(project_root_dir)
    elif 'web_assets:ts' == code_type:
        exit_code = _compile_web_assets_ts(project_root_dir, runlevel)
    elif 'web_assets:dist' == code_type:
        exit_code = _prep_client_dist_for_project(project_env, project_root_dir)
    elif 'all' == code_type:
        exit_code = _compile_python(project_root_dir)
        exit_code += _compile_web_assets(project_env, project_root_dir, runlevel)
    else:
        msg = 'Invalid compile target: '
        msg += "'" + str(code_type) + "', options are: "
        msg += str(VALID_CODE_TYPES)
        raise Exception(msg)
    return exit_code

def _compile_python(project_root_dir):
    try:
        from pylint.lint import Run
        rcfile = os.path.join(project_root_dir, '.pylintrc')
        cmd = 'pylint '
        cmd += '--errors-only '
        cmd += '--rcfile ' +  rcfile 
        cmd += ' nest_py'
        cr = container_users.make_host_user_command_runner()
        res = cr.run(cmd, stream_log=True)
        exit_code = res.get_exit_code()
    except Exception as e:
        log("linting crashed: " + str(e))
        traceback.print_exc()
        exit_code = 1
    return exit_code

def load_libsrc():
    """
    loads directories in 'nest_py/lib_src' into the sys path.
    TODO: needs to automatically pick up new directories,
    currently hardcode
    """
    import sys
    ops_dir = os.path.dirname(os.path.realpath(__file__))
    fst_package = ops_dir + '/../lib_src/fst_pipeline'
    sys.path.append(fst_package)
    return

def _compile_web_assets_npm(project_root_dir):
    """(Re)install the node modules."""
    clientdir = os.path.join(project_root_dir, 'client')
    modulesdir = os.path.join(clientdir, 'node_modules')
    if os.path.isdir(modulesdir):
        log("removing " + str(modulesdir))
        try:
            rmtree(modulesdir)
        except OSError as exception:
            log(exception.strerror + ": " + exception.filename)
            return 1
    log("installing node modules under " + str(clientdir))
    cmd = 'npm i'
    cr = container_users.make_host_user_command_runner()
    cr.set_working_dir(clientdir)
    res = cr.run(cmd, stream_log=True)
    return res.get_exit_code()

def _compile_web_assets_ts(project_root_dir, runlevel):
    """Build the client assets."""
    clientdir = os.path.join(project_root_dir, 'client')
    gulppath = os.path.join(clientdir, 'node_modules', '.bin', 'gulp')
    log("running gulp from " + str(clientdir))
    exit_sum = 0
    # clean and build
    cr = container_users.make_host_user_command_runner()
    cr.set_working_dir(clientdir)
    
    # Pass runlevel down into gulp
    runlevel.write_to_os()
    
    # Pass HUBZERO_APPLICATION_HOST and MAX_CONTENT_LENGTH
    # down into gulp (knoweng only)
    project_params = knoweng_config.generate_project_params(runlevel)
    hz_host = project_params['HUBZERO_APPLICATION_HOST']
    if hz_host != 'FIXME':
        os.environ['HUBZERO_APPLICATION_HOST'] = hz_host
    os.environ['MAX_CONTENT_LENGTH'] = str(project_params['MAX_CONTENT_LENGTH'])

    cmd = gulppath + " clean"
    res = cr.run(cmd, stream_log=True)
    exit_sum += res.get_exit_code()

    cmd = gulppath + " dist"
    res = cr.run(cmd, stream_log=True)
    exit_sum += res.get_exit_code()

    return exit_sum

def _prep_client_dist_for_project(project_env, project_root_dir):
    """
    currently this just means copying from index.<project_name>.html
    to index.html in the client dist directory.
    """
    #need to make the project's index.html the index.html that tomcat will find
    clientdir = os.path.join(project_root_dir, 'client')
    index_target_fn = os.path.join(clientdir, 'index.html')

    index_src_base = 'index.' + project_env.get_project_name() + '.html'
    index_src_fn = os.path.join(clientdir, index_src_base)
    cmd = 'cp ' + index_src_fn + ' ' + index_target_fn
    cr = container_users.make_host_user_command_runner()
    result = cr.run(cmd)
    return result.get_exit_code()

def _compile_web_assets(project_env, project_root_dir, runlevel):
    """Install client dependencies and build the client assets."""
    exit_sum = 0
    exit_sum += _compile_web_assets_npm(project_root_dir)
    exit_sum += _compile_web_assets_ts(project_root_dir, runlevel)
    exit_sum += _prep_client_dist_for_project(project_env, project_root_dir)
    return exit_sum
