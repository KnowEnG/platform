import os
import nest_py.core.jobs.file_utils as file_utils

import nest_py.core.jobs.file_space.run_file_space as run_file_space
from nest_py.core.jobs.file_space.run_file_space import RunFileSpace
from nest_py.core.data_types.nest_id import NestId

RUNS_AGG_DIR='runs'

class JobFileSpace(object):
    """
    Maps to the working directory of a type of job (all available 
    versions of the config file, and all runs of the job
    will be contained within the JobFileSpace's directory).
    """

    def __init__(self, wix_file_space, job_key, ensure=False):
        self.wix_fs = wix_file_space
        self.job_key = job_key
        self.current_run_fs = None
        if ensure:
            self.get_dirpath(ensure=True)
        return

    def get_dirpath(self, ensure=False):
        wix_root = self.wix_fs.get_dirpath()
        dirpath = os.path.join(wix_root, self.job_key)
        if ensure:
            file_owner = self.get_file_owner()
            file_utils.ensure_directory(dirpath, file_owner)
            self.get_configs_dirpath(ensure=True)
            self.get_runs_dirpath(ensure=True)
            self.get_job_global_data_dir(ensure=True)
        return dirpath

    def get_job_key(self):
        return self.job_key

    def get_wix_fs(self):
        return self.wix_fs

    def get_file_owner(self):
        user = self.wix_fs.get_file_owner()
        return user

    def resolve_and_load_config(self, config_basename):
        """
        config_basename(str or None): the basename of a file
            in this job's 'configs/' directory, or None. If
            None, the default config file will be loaded if 
            it exists. If it does not exist, it will be
            initialized as empty and then used.

        returns the jdata that comes from loading the config file,
            which must be valid json (with comments allowed)
        """
        if config_basename is None:
            resolved_filepath = self._default_config_filepath()
            if not os.path.exists(resolved_filepath):
                print("No config found. Writing empty config file to: " + 
                    str(resolved_filepath))
                self._write_empty_default_config()
            resolved_basename = self._default_config_basename()
        else:
            resolved_basename = config_basename
        jdata = self.load_job_config(resolved_basename)
        return jdata

    def get_run_file_space(self, run_id, ensure=False):
        run_fs = RunFileSpace(self, run_id, ensure=ensure)
        return run_fs

    def set_current_run(self, run_file_space):
        """
        set the given RunFileSpace as the 'current', which results
        in a symlink from the run's directory to <job_key>/current_run
        """
        self.current_run_fs = run_file_space

        #create symlink 
        job_dir = self.get_dirpath()
        abs_run_dir = run_file_space.get_dirpath()
        #we must use a relative pathname because the symlink is created
        #inside the docker container (in the /code_live/ directory), and
        #we want it to be valid outside the container
        rel_run_dir= os.path.relpath(abs_run_dir, job_dir)
        target_dir_link = os.path.join(job_dir, 'current_run')
        file_owner = self.get_file_owner()
        if os.path.islink(target_dir_link):
            os.remove(target_dir_link)
        file_utils.make_symlink(rel_run_dir, target_dir_link, file_owner)
        return

    def get_job_global_data_dir(self, ensure=False):
        job_dir = self.get_dirpath()
        d = os.path.join(job_dir, 'cross_run_data')
        if ensure:
            file_owner = self.get_file_owner()
            file_utils.ensure_directory(d, file_owner=file_owner)
        else:
            if not os.path.exists(d):
                raise Exception('job global data dir does not exist: ' + d)
        return d

    def get_parent_wix_fs(self):
        return self.wix_fs

    def get_configs_dirpath(self, ensure=False):
        job_dir = self.get_dirpath()
        d = os.path.join(job_dir, 'configs')
        if ensure:
            fo = self.get_file_owner()
            file_utils.ensure_directory(d, file_owner=fo)
        else:
            if not os.path.exists(d):
                raise Exception('job configs/ dir does not exist: ' + d)
        return d

    def get_runs_dirpath(self, ensure=False):
        job_dir = self.get_dirpath()
        d = os.path.join(job_dir, 'runs')
        if ensure:
            fo = self.get_file_owner()
            file_utils.ensure_directory(d, file_owner=fo)
        else:
            if not os.path.exists(d):
                raise Exception('job configs/ dir does not exist: ' + d)
        return d

    def load_job_config(self, config_basename):
        """
        """
        configs_dir = self.get_configs_dirpath()
        filepath = os.path.join(configs_dir, config_basename)

        #TODO: don't remember why this much error checking was needed, but
        #maybe it should be a utility method in file_utils
        if os.path.exists(filepath):
            if os.path.exists(filepath):
                if not os.path.isfile(filepath):
                    raise Exception('Found config file path, but was a directory')
                if not os.access(filepath, os.R_OK):
                    raise Exception("Don't have permission to read config file: "
                        + filepath)
            else:
                raise Exception("Specified config file not found: " + filepath)

        config_jdata = file_utils.load_json_file_with_comments(filepath)
        return config_jdata

    def _default_config_basename(self):
        basename = self.job_key + '.cfg'
        return basename

    def _default_config_filepath(self):
        bn = self._default_config_basename()
        configs_dir = self.get_configs_dirpath()
        config_filepath = os.path.join(configs_dir, bn)
        return config_filepath

    def _write_empty_default_config(self):
        """
        when the default config file doesn't exist, write an empty config to it
        """
        fp = self._default_config_filepath()
        empty_cfg = dict()
        owner = self.get_file_owner()
        file_utils.dump_json_file(fp, empty_cfg, file_owner=owner)
        return 

        
