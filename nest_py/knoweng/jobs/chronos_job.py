"""This module defines constants and a base class for knoweng analytics jobs
   that run remotely on mesos via chronos.
"""

import logging
import os
from string import Template
from time import sleep

import requests

# this is the logger configured for nest_jobs. TODO clean up logging everywhere
LOGGER = logging.getLogger('rq.worker')

class ChronosJob(object):
    """Base class for analytics jobs that run remotely on mesos via chronos."""

    # TODO move into config
    cloud_mesos_dict = {
        'aws': 'fixme.yourhost.com:4400'
    }
    """Map from cloud name to mesos host."""
    # TODO move into config
    cloud_path_dict = {
        'aws': '/mnt/knowdev/YOUR_NET_ID'
    }
    """Map from cloud name to redis host."""
    # TODO move into config
    cloud_redis_dict = {
        'aws': {
            'host': 'fixme.yourhost.com',
            'port': 6379,
            'password': 'GARBAGESECRET'
        }
    }
    """Map from cloud name to top level of worker node storage."""

    def __init__(self, user_id, job_id, userfiles_dir, job_dir_relative_path, \
        job_name, timeout, cloud, docker_image, num_cpus, max_ram_mb):
        """Initializes self.

        Args:
            user_id (NestId): The user id associated with the job.
            job_id (NestId): The job id associated with the job.
            userfiles_dir (str): The base directory containing all files for
                all users.
            job_dir_relative_path (str): The relative path from userfiles_dir
                to the directory containing the job's files.
            job_name (str): A name to identify the job in mesos.
            timeout (int): The maximum execution time in seconds.
            cloud (str): The cloud name, which must appear as a key in
                cloud_path_dict.
            docker_image (str): The docker image name for chronos to run.
            num_cpus (int): The number of CPUs to allocate for the job.
            max_ram_mb (int): The maximum RAM in megabytes to allocate for the
                job.

        Returns:
            None: None.

        """

        self.user_id = user_id
        self.job_id = job_id
        self.userfiles_dir = userfiles_dir
        self.job_dir_relative_path = job_dir_relative_path
        self.job_dir_path = os.path.join(userfiles_dir, job_dir_relative_path)
        self.job_name = job_name
        self.timeout = timeout
        self.cloud = cloud
        self.docker_image = docker_image
        self.num_cpus = num_cpus
        self.max_ram_mb = max_ram_mb
        self.started = False

    def start(self):
        """Submits the job to chronos. Runs command from self.get_command in the
        remote docker container.

        Returns:
            None: None.

        """
        self.started = True
        # call Chronos
        command_wrapper_template = Template(
            "timeout -s 9 ${timeout_secs}s sh -c '{ ${command} } 2> " + \
            ChronosJob.cloud_path_dict[self.cloud] + \
            "/logs/${job_name}; '")

        command_wrapper = command_wrapper_template.substitute({
            "timeout_secs": self.timeout,
            "command": self.get_command(),
            "job_name": self.job_name
        })

        payload = {
            "schedule": "R1//P3M",
            "name": self.job_name,
            "container": {
                "type": "DOCKER",
                "image": self.docker_image,
                "volumes": [{
                    "containerPath": ChronosJob.cloud_path_dict[self.cloud] + "/",
                    "hostPath": ChronosJob.cloud_path_dict[self.cloud] + "/",
                    "mode":"RW"
                }]
            },
            "retries": "1",
            # TODO revisit these settings
            "cpus": str(self.num_cpus),
            "mem": str(self.max_ram_mb),
            "command": command_wrapper
        }
        # submit to chronos
        requests.post('http://' + ChronosJob.cloud_mesos_dict[self.cloud] + \
                      '/scheduler/iso8601',
                      json=payload)

    def get_command(self):
        """Returns the command to run in the remote docker container.

        Returns:
            str: The command to run in the remote docker container.

        """
        raise NotImplementedError('Subclass must override base class method.')

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

    def is_done(self):
        """Returns True if the job is done, else returns False. Subclasses
        must implement.

        Returns:
            boolean: True if the job is done, else False.

        """
        raise NotImplementedError('Subclass must override base class method.')

    def on_done(self):
        """Processes job outputs. Subclasses must implement.

        Returns:
            None: None.

        """
        raise NotImplementedError('Subclass must override base class method.')

    def delete_from_chronos(self):
        """Calls the Chronos API to delete its record of this job.

        Returns:
            None: None.

        """
        delete_from_chronos_by_name(self.job_name, self.cloud)

def delete_from_chronos_by_name(job_name, cloud):
    """Given a job's name, deletes it from Chronos.

    Args:
        job_name (str): The name of job in Chronos.
        cloud (str): The cloud name, which must appear as a key in
            cloud_path_dict.

    Returns:
        None: None.

    """
    requests.delete('http://' + ChronosJob.cloud_mesos_dict[cloud] + \
        '/scheduler/job/' + job_name)

def get_all_chronos_job_names(cloud):
    """Returns all job names known to Chronos.

    Args:
        cloud (str): The cloud name, which must appear as a key in
            cloud_path_dict.

    Returns:
        list(str): A list of job names.

    """
    url = 'http://' + ChronosJob.cloud_mesos_dict[cloud] + '/scheduler/jobs/'
    # rarely, under load, chronos will return a 500; we'll want to retry
    num_attempts = 10
    attempt_wait_seconds = 10
    return_val = []
    for attempt in range(0, num_attempts):
        chronos_response = requests.get(url)
        # only error I've ever seen is a 500; if this code path ends up failing
        # on others, we'll examine the logs and figure out the right way to
        # handle
        if chronos_response.status_code != 500:
            return_val = [job['name'] for job in chronos_response.json()]
            break
        LOGGER.warning('Chronos returned 500 on attempt ' + str(attempt) + \
            '. Retrying in ' + str(attempt_wait_seconds) + ' seconds.')
        sleep(attempt_wait_seconds)
    return return_val
