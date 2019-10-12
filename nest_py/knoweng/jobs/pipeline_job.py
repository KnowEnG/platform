"""This module defines constants and a base class for knoweng analytics jobs
   that run remotely on a distributed compute cluster. Supports the EXEC_MODE
   environment configuration.

   When the EXEC_MODE environment variable has been explicitly configured
   with a value of "kubernetes", use the KubernetesExecutor.

   Otherwise, fall back to using the ChronosExecutor.
"""

from abc import ABCMeta, abstractmethod
import logging
import os
import re

if os.getenv('EXEC_MODE', 'chronos') == 'kubernetes':
    from nest_py.knoweng.jobs.kubernetes_executor import KubernetesExecutor
    EXECUTOR_CLASS = KubernetesExecutor
else:
    from nest_py.knoweng.jobs.chronos_executor import ChronosExecutor
    EXECUTOR_CLASS = ChronosExecutor

LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.WARNING)

class PipelineJob(object):
    """Base class for analytics jobs that run remotely via the chosen
    ExecutionEngine."""

    __metaclass__ = ABCMeta

    def __init__(self, user_id, job_id, project_id, userfiles_dir, \
        job_dir_relative_path, job_name, timeout, cloud, docker_image, \
        num_cpus, max_ram_mb):
        """Initializes self.

        Args:
            user_id (NestId): The user id associated with the job.
            job_id (NestId): The job id associated with the job.
            project_id (NestId): The project id associated with the job.
            userfiles_dir (str): The base directory containing all files for
                all users.
            job_dir_relative_path (str): The relative path from userfiles_dir
                to the directory containing the job's files.
            job_name (str): A name to identify the job in mesos.
            timeout (int): The maximum execution time in seconds.
            cloud (str): The cloud name, which must appear as a key in
                cloud_path_dict.
            docker_image (str): The docker image name for chronos to run.
            num_cpus (int): The number of CPUs to allocate for the job. Note
                AWS m4.xl is 4 CPUs.
            max_ram_mb (int): The maximum RAM in megabytes to allocate for the
                job. Note AWS m4.xl is 16 GB.

        Returns:
            None: None.

        """

        self.user_id = user_id
        self.job_id = job_id
        self.project_id = project_id
        self.userfiles_dir = userfiles_dir
        self.job_dir_relative_path = job_dir_relative_path
        self.job_dir_path = os.path.join(userfiles_dir, job_dir_relative_path)
        self.job_name = job_name
        if re.search('[A-Z]', job_name) is not None:
            raise ValueError('Job name cannot contain capital letters. Got ' + \
                job_name)
        if re.search('_', job_name) is not None:
            raise ValueError('Job name cannot contain underscores. Got ' + \
                job_name)
        self.timeout = timeout
        self.cloud = cloud
        self.docker_image = docker_image
        self.num_cpus = num_cpus
        self.max_ram_mb = max_ram_mb
        self.started = False

        self.execution_engine = EXECUTOR_CLASS(job_name, timeout, cloud, \
            docker_image, num_cpus, max_ram_mb)

    def start(self):
        """Submits the job to the executor. Runs command from self.get_command()
        in the remote docker container.

        Returns:
            None: None.

        """
        LOGGER.debug('Attempting to start ' + self.job_name + '...')
        self.started = True
        return self.execution_engine.start(self.get_command())

    @abstractmethod
    def get_command(self):
        """Returns the command to run in the remote docker container.

        Returns:
            str: The command to run in the remote docker container.

        """
        raise NotImplementedError('Subclass must override base class method.')

    @abstractmethod
    def is_ready(self):
        """Returns True if the job is ready to start, else returns False.
        Subclasses must implement.

        Returns:
            boolean: True if the job is ready to start, else False.

        """
        raise NotImplementedError('Subclass must override base class method.')

    def is_started(self):
        """Returns True if the job has been started, else returns False. Note
        this will continue to return True even after the job has finished.
        Subclasses generally should not implement.

        Returns:
            boolean: True if the job has been started, else False.

        """
        return self.started

    def is_failed(self):
        """Returns True if the job has failed, else returns False.

        Returns:
            boolean: True if the job has failed, else False.

        """
        return False

    def get_error_message(self):
        """Returns the error message if this job has failed, else returns None.

        Returns:
            str: The error message if this job has failed, else None.

        """
        return None

    @abstractmethod
    def is_done(self):
        """Returns True if the job is done, else returns False. Subclasses
        must implement.

        Returns:
            boolean: True if the job is done, else False.

        """
        raise NotImplementedError('Subclass must override base class method.')

    @abstractmethod
    def on_done(self):
        """Processes job outputs. Subclasses must implement.

        Returns:
            None: None.

        """
        raise NotImplementedError('Subclass must override base class method.')

    def delete_job_record(self):
        return self.execution_engine.delete()

    @staticmethod
    def get_cloud_path(cloud):
        """FIXME any reason to keep this parameterized static instead of instance?"""
        return EXECUTOR_CLASS.cloud_path_dict[cloud]

    @staticmethod
    def get_cloud_redis_dict(cloud):
        # TODO move to config
        # TODO use in-cluster redis
        return {
            'aws': {
                'host':  os.getenv('AWS_REDIS_HOST', 'redis'),
                'port': os.getenv('AWS_REDIS_PORT', 6379),
                'password': os.getenv('AWS_REDIS_PASS', 'GARBAGESECRET')
            }
        }[cloud]
