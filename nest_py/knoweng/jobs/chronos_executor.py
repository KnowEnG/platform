"""This module defines constants and a base class for knoweng analytics jobs
   that run remotely on mesos via chronos.
"""

import logging
import os
from string import Template
from nest_py.knoweng.jobs.abstract_executor import AbstractExecutor, \
    is_response_ok, retry_request_until_ok

import requests

LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.WARNING)
VERBOSE = False

class ChronosExecutor(AbstractExecutor):
    """Base class for analytics jobs that run remotely on mesos via chronos."""

    # TODO move into config
    cloud_master_dict = {
        'aws': os.getenv('AWS_MESOS_MASTER', 'knowdevmaster01.knoweng.org:4400')
    }
    """Map from cloud name to mesos host."""

    # TODO move into config
    cloud_path_dict = {
        'aws': os.getenv('AWS_SHARED_MNT_PATH', '/mnt/knowdev')
    }
    """Map from cloud name to top level of worker node storage."""

    def __init__(self, job_name, timeout, cloud, docker_image, \
        num_cpus, max_ram_mb):
        """Initializes self.

        Args:
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
        self.job_name = job_name
        self.timeout = timeout
        self.cloud = cloud
        self.docker_image = docker_image
        self.num_cpus = num_cpus
        self.max_ram_mb = max_ram_mb

    def start(self, command):
        """Submits the job to chronos. Runs command in the remote docker
        container.

        Args:
            command (str): The command to run inside of the container.

        Returns:
            None: None.

        """
        LOGGER.info("Starting ChronosExecutor for " + str(self.job_name))

        # call Chronos
        command_wrapper_template = Template(
            "timeout -s 9 ${timeout_secs}s sh -c '{ ${command} } 2> " + \
            ChronosExecutor.cloud_path_dict[self.cloud] + \
            "/logs/${job_name}; '")

        command_wrapper = command_wrapper_template.substitute({
            "timeout_secs": self.timeout,
            "command": command,
            "job_name": self.job_name
        })

        payload = {
            "schedule": "R1//P3M",
            "name": self.job_name,
            "container": {
                "type": "DOCKER",
                "image": self.docker_image,
                "volumes": [{
                    "containerPath": ChronosExecutor.cloud_path_dict[self.cloud] + "/",
                    "hostPath": ChronosExecutor.cloud_path_dict[self.cloud] + "/",
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
        response = requests.post(\
            'http://' + ChronosExecutor.cloud_master_dict[self.cloud] + \
            '/scheduler/iso8601',
            json=payload)
        is_response_ok(response, 1, -1)

    def delete(self):
        """Deletes the job from Chronos.


        Returns:
            None: None.

        """
        requests.delete('http://' + \
            ChronosExecutor.cloud_master_dict[self.cloud] + \
            '/scheduler/job/' + self.job_name)

    @staticmethod
    def get_all_job_names(cloud):
        """Returns all job names known to Chronos.

        Args:
            cloud (str): The cloud name, which must appear as a key in
                cloud_path_dict.

        Returns:
            list(str): A list of job names.

        """
        url = 'http://' + ChronosExecutor.cloud_master_dict[cloud] + '/scheduler/jobs/'
        # rarely, under load, chronos will return a 500; we'll want to retry
        request_lambda = lambda: requests.get(url)
        response = retry_request_until_ok(request_lambda, 10, 10)
        return_val = []
        if response is not None:
            return_val = [job['name'] for job in response.json()]
        return return_val
