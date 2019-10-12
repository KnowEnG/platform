"""
Entrypoint into the Wix runtime environment. Holds a reference
to where all the wix job 'run' commands are and then also the
main method for starting up one of those jobs using Wix (including
all of the Wix runtime infrastructure like managing the working
directories and database entries for wix_run and nest_users).
"""

import os
import traceback
import nest_py.core.jobs.file_utils as file_utils
import nest_py.ops.container_users as container_users
import nest_py.wix.wix_db as wix_db

import nest_py.wix.jobs.hello_world0 as hello_world0
import nest_py.omix.jobs.cral.import_features_csv_example as import_features_csv_example

from nest_py.core.jobs.job_context import JobContext
from nest_py.core.jobs.file_space.wix_file_space import WixFileSpace
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
    'import_features_csv_example':import_features_csv_example.run,
}

def valid_job_keys():
    return COMMAND_LOOKUP.keys()

def run(job_key, config_basename, wix_data_dir):
    """
    entry into the wix environment to trigger a job

    config_basename(string) is a filename or None

    wix_data_dir (string) is a directory name that all data
        from all jobs will be put into, organized by
        job name and run
    """
    start_time = CheckpointTimer.current_time()

    jcx = _make_job_context(job_key, config_basename, wix_data_dir)
    wix_db.init_db_resources(jcx)
    wix_db.write_job_start(jcx)

    jcx.log(
        "\n WIX RUNNER : START " +
        "\n job        : " + job_key +
        "\n wix run id : " + str(jcx.get_wix_run_id()) +
        "\n results dir: " + jcx.get_run_file_space().get_dirpath())

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
    wix_db.write_job_end(jcx)

    jcx.log("\n WIX RUNNER   : FINISHED " +
        "\n job          : " + job_key +
        "\n wix runid    : " + str(jcx.get_wix_run_id()) +
        "\n results dir  : " + jcx.get_run_file_space().get_dirpath() +
        "\n took         : " + str(formatted_secs))
    return exit_code

def _make_job_context(job_key, config_rel_filename, wix_data_dir):

    #wix jobs run as the linux user running the commands
    #at the commandline
    jcx_user = container_users.make_host_user_container_user()

    wix_fs = WixFileSpace(wix_data_dir, jcx_user)
    job_fs = wix_fs.get_job_file_space(job_key, ensure=True)
    config_jdata = job_fs.resolve_and_load_config(config_rel_filename)

    jcx = JobContext(job_key, jcx_user, job_fs, config_jdata, log_to_stdout=True)

    return jcx
