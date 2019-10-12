
import os
import nest_py.core.jobs.file_utils as file_utils

RUN_DIR_PREFIX = 'run_'
#number of digits to left pad rundir indexes to
RUN_DIR_SIG_DIGITS = 3

class RunFileSpace(object):
    """
    Maps to the working directory of a single run of a job.
    Manages the location of the log file and config file
    of the run (within the working directory).
    """

    def __init__(self, job_file_space, wix_run_id, ensure=False):
        self.wix_run_id = wix_run_id
        self.job_fs = job_file_space
        if ensure:
            self.get_dirpath(ensure=True)
        return

    def get_job_fs(self):
        """
        """
        return self.job_fs

    def get_wix_run_id(self):
        """
        Gets the NestId assocatied with the current run. This
        is the LOCAL identifier of the data directory on the
        local disk, not the wix_run_id in the database. 
        FIXME:this needs to be reconciled so the db and local
        disk NestId's are the same.
        """
        return self.wix_run_id

    def get_dirpath(self, ensure=False):
        run_idx = self.wix_run_id.get_value()
        basename = _run_dir_basename(run_idx)
        job_dirpath = self.job_fs.get_runs_dirpath()
        dirpath = os.path.join(job_dirpath, basename)
        if ensure:
            fo = self.get_file_owner()
            file_utils.ensure_directory(dirpath, fo)
        return dirpath

    def write_config_copy(self, jdata):
        fn = self.get_config_filepath()
        file_owner = self.get_file_owner()
        file_utils.dump_json_file(fn, jdata, file_owner=file_owner)
        return

    def get_file_owner(self):
        """
        Gets the ContainerUser that created the directory on disk
        (and probably should own any files that are written
        to this run's directory).
        """
        user = self.job_fs.get_file_owner()
        return user

    def get_config_filepath(self):
        """
        returns absolute filepath to this run's copy of the
        config it's using. Note this is where the archived copy
        of the config goes, not the original source file.
        """
        dirp = self.get_dirpath()
        basename = self.job_fs.get_job_key() + '.cfg.json'
        fp = os.path.join(dirp, basename )
        return fp

    def get_log_filepath(self):
        """
        absolute filepath of this run's log file
        """
        dirp = self.get_dirpath()
        basename = self.job_fs.get_job_key() + '.log'
        fp = os.path.join(dirp, basename)
        return fp

def _deduce_next_run_idx(run_aggs_dir, sig_digits=RUN_DIR_SIG_DIGITS):
    prefix_len = len(RUN_DIR_PREFIX)
    existing_run_dirs = list()
    for basename in os.listdir(run_aggs_dir):
        start_of_basename = basename[0:prefix_len]
        if start_of_basename == RUN_DIR_PREFIX:
            existing_run_dirs.append(basename)

    next_run_idx = 0
    for existing_dir in existing_run_dirs:
        run_idx_str = existing_dir[prefix_len:]
        run_idx = int(run_idx_str)
        if run_idx >= next_run_idx:
            next_run_idx = run_idx + 1
    return next_run_idx

def _run_dir_basename(run_index):
    #pad with leading zeros
    run_suffix = str(run_index).zfill(RUN_DIR_SIG_DIGITS)
    run_basename = RUN_DIR_PREFIX + run_suffix
    return run_basename

