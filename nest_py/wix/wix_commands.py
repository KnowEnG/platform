import os
import traceback
import nest_py.core.jobs.file_utils as file_utils
import nest_py.ops.container_users as container_users
import nest_py.wix.jobs.hello_world0 as hello_world0

from nest_py.core.jobs.job_context import JobContext
from nest_py.core.jobs.job_file_space import JobRunFileSpace
from nest_py.core.jobs.checkpoint import CheckpointTimer

#this is where you add new commands to make them
#available to use with './nest_ops wix <wix_job>'
#you also need to add an import above.
#note the keys are all just strings that are never parsed,
#but we use a convention of <project>.<algo_key>
#the values are names of a method in the given python source
#code file
COMMAND_LOOKUP = {
    'hello_world.0': hello_world0.run,
}

def run(job_key, config_abs_filename, wix_data_dir):
    """
    entry into the wix environment to trigger a job

    config_abs_filename (string) is a filename or None

    wix_data_dir (string) is a directory name that all data
        from all jobs will be put into, organized by
        job name and run
    """
    start_time = CheckpointTimer.current_time()
    jcx = _make_job_context(job_key, config_abs_filename, wix_data_dir)
    _symlink_current_run(jcx)
    _write_config_copy_to_rundir(jcx)
    jcx.log("WIX RUNNER: Running job '" + job_key + "', run at: '" +
        jcx.get_run_dir() + ', start time = ' + str(start_time))

    if job_key in COMMAND_LOOKUP:
        try: 
            COMMAND_LOOKUP[job_key](jcx)
            if jcx.succeeded():
                exit_code = 0 #success exit code
            else:
                exit_code = 1
        except Exception as e:
            stacktrace = traceback.format_exc()
            jcx.log('Exception = ' + str(e))
            jcx.log(str(stacktrace))
            exit_code = 1
    else:
        jcx.log('not a valid wix command')
        exit_code = 1
    if exit_code == 0:
        status = 'SUCCESS'
    else:
        status = 'FAILURE'
    elapsed_secs = CheckpointTimer.current_time() - start_time
    formatted_secs = CheckpointTimer.format_elapsed_secs(elapsed_secs)
    jcx.log("WIX RUNNER complete: (" + status + ") Took: " + formatted_secs)
    return exit_code
    
def valid_job_keys():
    return COMMAND_LOOKUP.keys()

def _make_job_context(job_key, config_filename, wix_data_dir):
    #wix jobs run as the linux user running the commands
    #at the commandline
    jcx_user = container_users.make_host_user_container_user()

    file_space = JobRunFileSpace(wix_data_dir, job_key, jcx_user)

    #force the global data dir to be created if it isn't there
    file_space.get_job_global_data_dir()

    config_jdata = _resolve_config_file(config_filename, job_key, wix_data_dir, jcx_user)
    jcx = JobContext(job_key, jcx_user, file_space, config_jdata,
        log_stdout=True)
    return jcx

def _resolve_config_file(config_filename, job_key, wix_data_dir, jcx_user):
    """
    if the config file is not None, loads it.

    If config file is None, looks for the config file for the job 
    in the default location.
    If it's not there, creates a config file with no parameters and
    writes it.
    Returns either the config (jdata) from the file or an empty
    dictionary to indicate no config.

    Raises exception if a config file was explicitly given but
    can't be read.
    """
    if config_filename is None:
        resolved_filename = _default_config_filename(job_key, wix_data_dir)
        if not os.path.exists(resolved_filename):
            #if the default config file doesn't exist, write an empty config to it
            empty_config = dict()
            file_utils.dump_json_file(resolved_filename, empty_config, 
                file_owner=jcx_user)
            print("No config found. Writing empty config file to: " + 
                str(resolved_filename))
    else:
        resolved_filename = config_filename

    if os.path.exists(resolved_filename):
        if not os.path.isfile(resolved_filename):
            raise Exception('Found config file path, but was a directory')
        if not os.access(resolved_filename, os.R_OK):
            raise Exception("Don't have permission to read config file: "
                + resolved_filename)
    else:
        raise Exception("Specified config file not found: " + resolved_filename)

    config_jdata = file_utils.load_json_file(resolved_filename)
    return config_jdata

def _default_config_filename(job_key, wix_data_dir):
    basename = job_key + '.cfg'
    fn = os.path.join(wix_data_dir, job_key, basename)
    return fn
    
def _symlink_current_run(jcx):
    """
    creates a file link from the name of the current run's files (called
    something like 'jobkey/run_00x/') to 'jobkey/current_run'
    """
    numbered_dir_name = os.path.basename(jcx.get_run_dir())
    job_dir = jcx.get_parent_job_dir()
    target_dir_link = os.path.join(job_dir, 'current_run')
    jcx_user = jcx.get_container_user()
    if os.path.exists(target_dir_link):
        os.remove(target_dir_link)
    file_utils.make_symlink(numbered_dir_name, target_dir_link, jcx_user)
    return

def _write_config_copy_to_rundir(jcx):
    """
    writes a copy of the config that was used to the run's directory
    alongside the run's logfile.
    """
    jdata = jcx.get_config_jdata()
    if not jdata is None:
        config_basename = jcx.get_job_key() + '.cfg.json'
        run_dir = jcx.get_run_local_data_dir()
        config_copy_fn = os.path.join(run_dir, config_basename)
        jcx_user = jcx.get_container_user()
        file_utils.dump_json_file(config_copy_fn, jdata, 
            file_owner=jcx_user)
    return

