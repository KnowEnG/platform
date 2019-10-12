import logging
import os
import sys
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

    def __init__(self, job_key, container_user, job_file_space,
        config_jdata, log_to_stdout=True):

        self.job_key = job_key
        self.run_file_space = None
        self.job_file_space = job_file_space
        self.container_user = container_user
        self.log_manager = NestRunLogManager(job_key, log_to_stdout=log_to_stdout)
        self.success = None
        self.config_jdata = config_jdata
        self.runtime_objects = dict()
        self.timer = CheckpointTimer(job_key)
        self.wix_run_tle = None
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

    def get_wix_run_id(self):
        return self.get_wix_run_tle().get_nest_id()

    def get_wix_run_tle(self):
        return self.wix_run_tle

    def set_runtime_object(self, name, obj):
        self.runtime_objects[name] = obj
        return

    def runtime(self):
        return self.runtime_objects

    def get_wix_file_space(self):
        """
        gets the toplevel WixFileSpace object that manages all
        files for all jobs in the current wix installation
        """
        return self.get_job_file_space().get_wix_fs()

    def get_job_file_space(self):
        """
        gets the JobFileSpace of that manages the files of all
        jobs that share the current job's 'job_key'.
        Same as self.get_wix_file_space().get_job_file_space(self.get_job_key())
        """
        return self.job_file_space

    def get_run_file_space(self):
        """
        gets teh RunFileSpace that manages the files of this particular
        job run.
        Same as self.get_job_file_space().get_run_file_space(self.get_wix_run_id())
        """
        return self.run_file_space

    def set_wix_run_tle(self, wix_run_tle):
        if not self.wix_run_tle is None:
            raise Exception("Wix Run Tablelike entry must only be set once per run")
        self.wix_run_tle = wix_run_tle
        wix_run_id = wix_run_tle.get_nest_id()
        job_fs = self.get_job_file_space()
        self.run_file_space = job_fs.get_run_file_space(wix_run_id, ensure=True)
        self.run_file_space.write_config_copy(self.get_config_jdata())
        job_fs.set_current_run(self.run_file_space)
        self.log_manager.add_file_space_target(self.run_file_space)
        return 

    def log(self, message):
        """
        logs a message to either a log file or stdout, 
        depending how this JobContext is configured.
        """
        self.log_manager.logger.debug(message)
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
        r = (self.success == True) or (self.success is None)
        return r
   

class NestRunLogManager(object):
    """
    Handles a single 'logger' with two targets: stdout and a logfile
    in a RunFileSpace of a job run.
    """

    def __init__(self, job_name, log_to_stdout=True):
        self.logger = logging.getLogger(job_name)

        # create formatter to add to the handlers
        self.formatter = logging.Formatter('[%(asctime)s] %(message)s')

        self.log_level = logging.DEBUG
        self.logger.setLevel(self.log_level)

        if log_to_stdout:
            self._add_stdout_target()
        return

    def _add_stdout_target(self):
        """
        meant to be used by the constructor, adds stdout
        as a target to write all log messages to
        """
        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(self.log_level)
        ch.setFormatter(self.formatter)
        self.logger.addHandler(ch)
        return

    def add_file_space_target(self, run_file_space):
        """
        run_file_space(RunFileSpace): 
        """
        log_fn = run_file_space.get_log_filepath()

        #https://docs.python.org/2/howto/logging-cookbook.html
        fh = logging.FileHandler(log_fn)
        fh.setLevel(self.log_level)

        fh.setFormatter(self.formatter)
        self.logger.addHandler(fh)
        return

