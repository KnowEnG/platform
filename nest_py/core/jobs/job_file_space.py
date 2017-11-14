import os

import nest_py.core.jobs.file_utils as file_utils

RUN_DIR_PREFIX = 'run_'
#number of digits to left pad rundir indexes to
RUN_DIR_SIG_DIGITS = 3

class JobRunFileSpace(object):
    """
    manages the directories available to job runs
    for a single type of job.

    Typical useage is that every 'run' gets a JobRunFileSpace
    initialized at the same root directory, and detects what
    the next run number is and initializes itself in a
    directory called myJob/run_<next_run_number>

    Eg.
        if initialized with non-existent root dir 'myJob', creates
        directory 'myJob', then '/home/myJob/run_000'.

        The next time a JobRunFileSpace is initialized with 'myJob',
        will create '/home/myJob/run_001'

        The complete directory layout will look like for one job
        with 2 runs.
        nest/data/wix/
            myJob/
                myJob.cfg  #default config file
                cross_run_data/ #job_global_data_dir, shared space between runs
                current_run/ #symlink to most recent run_XXX
                run_000/ #run_local_data_dir
                    myJob.log #log for run 000
                    myJob.cfg.json #config used by run 000
                run_001/
            
    """

    def __init__(self, root_dir, job_key, file_owner):
        """
        root_dir (string) root directory where jobs's files go
        
        job_key (string) unique to jobs of a type. some directories
            will be shared by runs, others will be unique to the
            run
        file_owner (ContainerUser) created directories will be owned
            by this user
        """
        self.root_dir = root_dir
        self.job_root_dir = os.path.join(root_dir, job_key)
        self.file_owner = file_owner
        file_utils.ensure_directory(self.job_root_dir, 
            file_owner=file_owner)

        self.run_idx = deduce_next_run_idx(self.job_root_dir)
        self.run_dir = make_run_dir(self.job_root_dir, self.run_idx)
        return

    def get_job_global_data_dir(self):
        """
        A directory that all runs of the current job type
        can access. Intended for storing raw data that is reused
        and cached results. 
        """
        d = os.path.join(self.job_root_dir, 'cross_run_data')
        file_utils.ensure_directory(d, file_owner=self.file_owner)
        return d

    def get_run_local_data_dir(self):
        """
        Directory that the current job run should write 
        run-specific results to. 
        """
        d = self.run_dir 
        file_utils.ensure_directory(d, file_owner=self.file_owner)
        return d

    def get_parent_job_dir(self):
        return self.job_root_dir

    def get_run_dir(self):
        """
        returns the same value as get_run_local_data_dir, but
        semantically this will always return the directory that
        contains all artifacts from a run (including the log 
        and config file copy made by JobContext), while
        run_local_data_dir is defined as the place a job
        can write files to.

        only the wix environment itself should use this method.
        """
        d = self.run_dir
        file_utils.ensure_directory(d, file_owner=self.file_owner)
        return d

    def get_external_job_dir(self, job_key):
        """
        get the 'parent_job_dir' of a job of any type that shares
        the same root directory as the currenty job. (e.g. all
        Wix jobs share the same root directory)
        """
        dirname = os.path.join(self.root_dir, job_key)
        return dirname

    def get_external_run_dir(self, job_key, run_index):
        """
        get the "run_local_data_dir" of a run of any type of
        job that shares the same root directory.
        (e.g in wix, if you want run 23 of a job named hello_world,
        this would return:
            dn = jcx.get_external_run_dir('hello_world', 23)
            dn == 'data/wix/hello_world/run_023'

        """
        job_dir = self.get_external_job_dir(job_key)
        run_base = _run_dir_basename(run_index)
        dirname = os.path.join(job_dir, run_base)
        if not os.path.exists(dirname):
            raise Exception('requested the dirname of a nonexistent run' +
                str(dirname))
        return dirname
        
    def get_run_idx(self):
        return self.run_idx

def deduce_next_run_idx(job_dir, sig_digits=3):
    prefix_len = len(RUN_DIR_PREFIX)
    existing_run_dirs = list()
    for basename in os.listdir(job_dir):
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

def make_run_dir(job_dir, next_run_idx):
    """
    """
    next_run_basename = _run_dir_basename(next_run_idx)
    next_run_dir = os.path.join(job_dir, next_run_basename)
    return next_run_dir

def _run_dir_basename(run_index):
    #pad with leading zeros
    run_suffix = str(run_index).zfill(RUN_DIR_SIG_DIGITS)
    run_basename = RUN_DIR_PREFIX + run_suffix
    return run_basename

    

