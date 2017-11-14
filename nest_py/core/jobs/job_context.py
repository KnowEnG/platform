import logging
import os
import sys
from nest_py.core.jobs.job_file_space import JobRunFileSpace
from nest_py.core.jobs.checkpoint import CheckpointTimer

class JobContext(object):
    """
    A context container for a job run. Provides logging, 
    tmp disk directory, system user, etc, to a single
    run of a job.

    Here we call the code that is configured to run
    as a single standalone instance a 'job', and each
    invocation of that code a 'run'.
    """

    def __init__(self, job_key, container_user, job_run_file_space,
        config_jdata, log_stdout=True):

        self.job_key = job_key
        self.file_space = job_run_file_space
        self.container_user = container_user
        self.logger = _setup_logger(job_key, job_run_file_space, log_stdout)
        self.success = None
        self.config_jdata = config_jdata
        self.runtime_objects = dict()
        self.timer = CheckpointTimer(job_key)
        return

    def get_job_key(self):
        return self.job_key

    def get_config_jdata(self):
        """
        Returns the JSON-style object (nested dicts, lists,
        strings, ints, and floats) associated with the job run.
        The particular data inside is not validated, it's 
        whatever was is the config file or input.
        """
        return self.config_jdata

    def set_runtime_object(self, name, obj):
        self.runtime_objects[name] = obj
        return

    def runtime(self):
        return self.runtime_objects

    def get_parent_job_dir(self):
        """
        the root directory that all jobs of this run's type
        share. Normally, job runs do not write to this directory
        directly. Instead, use get_job_global_data_dir to write
        data that has a scope across more than one run.
        """
        d = self.file_space.get_parent_job_dir()
        return d

    def get_job_global_data_dir(self):
        """
        Returns a (string) filename of the directory on
        the local filesystem shared by all jobs of the
        same type. Appropriate for raw data files that
        are loaded each run and for results cached 
        between runs.
        """
        d = self.file_space.get_job_global_data_dir()
        return d

    def get_run_dir(self):
        """
        returns the root dir of the current RUN. Prefer
        to put data in the get_run_local_data_dir, which
        is inside of here.
        """
        return self.file_space.get_run_dir()

    def get_run_id(self):
        """
        a relative identifier of the run. unique to the
        (job_key, vm it's running on).
        """
        return self.file_space.get_run_idx()

    def get_run_local_data_dir(self):
        """
        Returns a (string) filename of the data directory
        that the current run should use for results and
        temporary disk space during the run. A subdir
        of get_run_dir().
        """
        d = self.file_space.get_run_local_data_dir()
        return d

    def get_external_run_dir(self, job_key, run_index):
        """
        get the "run_local_data_dir" of a run of any type of
        job that shares the same root directory as this job
        (e.g in wix, if you want run 23 of a job named hello_world,
        this would return:
            dn = jcx.get_external_run_dir('hello_world', 23)
            dn == 'data/wix/hello_world/run_023'

        """
        dn = self.file_space.get_external_run_dir(job_key, run_index)
        return dn

    def log(self, message):
        """
        logs a message to either a log file or stdout, 
        depending how this JobContext is configured.
        """
        self.logger.debug(message)
        return 

    def checkpoint(self, message):
        """
        logs a message, but includes the time since
        the last checkpoint and the time since the
        job was triggered.
        """
        checkpoint_msg = self.timer._make_checkpoint_message(message)
        self.log(checkpoint_msg)
        return 

    def get_container_user(self):
        """
        Returns the ContainerUser that should do any system
        level (linux files and processes) work for the job.
        """
        return self.container_user

    def declare_success(self):
        """
        To be called by the job when it completes. The job
        runner will return a success exit-code to the commandline
        """
        self.success = True
        return

    def declare_failure(self):
        """
        To be called by the job when it completes. The job
        runner will return a Failure exit-code to the commandline
        """
        self.success = False
        return

    def succeeded(self):
        if self.success == None:
            self.log("WARNING: success/failure of the job run was \
                not declared, returning succeeded=True anyway.")
        r = (self.success == True)
        return r
    
def _setup_logger(job_name, file_space, log_stdout):
    """

    log_stdout(bool): if true, log messages to stdout as well
    as the log file. if false, log file only.
    """
    log_level = logging.DEBUG
    logger = logging.getLogger(job_name)
    logger.setLevel(log_level)
    log_fn = _make_log_filename(job_name, file_space)

    #https://docs.python.org/2/howto/logging-cookbook.html
    fh = logging.FileHandler(log_fn)
    fh.setLevel(log_level)

    # create formatter and add it to the handlers
    formatter = logging.Formatter('[%(asctime)s] %(message)s')
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    if log_stdout:
        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(log_level)
        ch.setFormatter(formatter)
        logger.addHandler(ch)

    return logger

def _make_log_filename(job_name, file_space):
    """
    file_space (JobRunFileSpace)
    """
    job_name = job_name.replace(' ', '_')
    run_dir = file_space.get_run_local_data_dir()
    log_fn = os.path.join(run_dir, 'wix_run.log')
    return log_fn
    
