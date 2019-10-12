import os

import nest_py.core.jobs.file_utils as file_utils
from nest_py.core.jobs.file_space.job_file_space import JobFileSpace

class WixFileSpace(object):
    """
    Maps to the root directory used by the wix runtime for all possible jobs.
    Manages the JobFileSpace objects that correspond to each job that wix
    knows how to run.

    """

    def __init__(self, wix_root_dir, file_owner, ensure=False):
        self.root_dir = wix_root_dir
        self.file_owner = file_owner

        if ensure:
            self.get_dirpath(ensure=True)
        elif not os.path.exists(wix_root_dir):
            raise Exception("Wix root data directory does not exist")
        return

    def get_dirpath(self, ensure=False):
        if ensure:
            fo = self.get_file_owner()
            file_utils.ensure_directory(self.root_dir, file_owner=fo)
        return self.root_dir

    def get_job_file_space(self, job_key, ensure=False):
        wix_fs = self
        job_fs = JobFileSpace(wix_fs, job_key, ensure=ensure)
        return job_fs

    def get_file_owner(self):
        return self.file_owner

