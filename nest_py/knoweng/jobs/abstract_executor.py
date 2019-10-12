"""This module defines a base class and methods for executors that run jobs
remotely.
"""

from abc import ABCMeta, abstractmethod
import logging
from time import sleep

import requests

LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.INFO)

class AbstractExecutor(object):
    """Base class for executor that runs jobs remotely."""

    __metaclass__ = ABCMeta

    @abstractmethod
    def __init__(self, job_name, timeout, cloud, docker_image, \
        num_cpus, max_ram_mb):
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
            num_cpus (int): The number of CPUs to allocate for the job. Note
                AWS m4.xl is 4 CPUs.
            max_ram_mb (int): The maximum RAM in megabytes to allocate for the
                job. Note AWS m4.xl is 16 GB.

        Returns:
            None: None.

        """
        raise NotImplementedError('AbstractExecutor is an abstract class. ' + \
            'Use a concrete subclass instead.')

    @abstractmethod
    def start(self, command):
        """Submits the job for remote execution. Runs command in the remote
        docker container.

        Args:
            command (str): The command to run inside the docker image.

        Returns:
            None: None.

        """
        raise NotImplementedError('Subclass must override base class method.')

    @abstractmethod
    def delete(self):
        """Deletes this job from the remote executor.

        Returns:
            None: None.

        """
        raise NotImplementedError('Subclass must override base class method.')

    # TODO in python 3.3+, we can decorate this with @abstractmethod, too
    # that decoration would go on the line after @staticmethod
    @staticmethod
    def get_all_job_names(cloud):
        """Returns all job names known to this executor.

        Args:
            cloud (str): The cloud name, which must appear as a key in
                cloud_path_dict.

        Returns:
            list(str): A list of job names.

        """
        raise NotImplementedError('Subclass must override base class method.')

def retry_request_until_ok(request_lambda, num_attempts, retry_delay_seconds):
    """Retries a request until either the request succeeds or num_attemps is
    exceeded.

    Args:
        request_lambda (lambda): A no-arg lambda that runs the request and
            returns the response.
        num_attemps (int): The maximum number of attempts to make.
        retry_delay_seconds (float): The number of seconds to wait between
            attempts.

    Returns:
        Response: A response object in the event of a successful request, else
            None.

    """
    return_val = None
    for attempt in range(0, num_attempts):
        response = request_lambda()
        ok = is_response_ok(response, attempt+1, retry_delay_seconds)
        if ok:
            return_val = response
            break
        sleep(retry_delay_seconds)
    return return_val

def is_response_ok(response, attempt_number, retry_delay_seconds):
    """Checks a response from a requests call for errors. Logs any errors and
    returns a boolean indicating success.

    Args:
        response (Response): The response from a requests call.
        attempt_number (int): The number of times the requests call has been
            attempted.
        retry_delay_seconds (float): The number of seconds until the next
            attempt, or None if there will be no next attempt.

    Returns:
        boolean: True if the response contains no HTTP error codes, else False.

    """
    return_val = False
    retry_msg = ''
    request_info = response.request.method + ' ' + response.request.url
    if retry_delay_seconds is not None:
        retry_msg = 'Retrying in ' + str(retry_delay_seconds) + ' seconds.'
    try:
        response.raise_for_status()
        # only error I've ever seen is a 500; if this code path ends up failing
        # on others, we'll examine the logs and figure out the right way to
        # handle
        if response.status_code == 500:
            LOGGER.warning('Request returned 500 on attempt ' + \
                str(attempt_number) + '. ' + retry_msg)
        else:
            return_val = True
    except requests.exceptions.HTTPError as http_err:
        LOGGER.debug('Response: ' + str(http_err))
        error_message = http_err.response.text
        LOGGER.debug(error_message)
        LOGGER.warning('Request returned ' + \
            str(http_err.response.status_code) + ' on attempt #' + \
            str(attempt_number) + ' for ' + request_info + '. ' + retry_msg)
    except requests.exceptions.Timeout as e1:
        # Maybe set up for a retry, or continue in a retry loop
        LOGGER.warning('Timed out on attempt #' + str(attempt_number) + \
            ' for ' + request_info + '. ' + retry_msg)
    except requests.exceptions.TooManyRedirects as e2:
        # Tell the user their URL was bad and try a different one
        LOGGER.warning('Too many redirects on attempt #' + \
            str(attempt_number) + ' for ' + request_info + '. ' + retry_msg)
    except requests.exceptions.RequestException as e3:
        # catastrophic error. bail.
        LOGGER.warning('Unknown error encountered on attempt #' + \
            str(attempt_number) + ' for ' + request_info + '. ' + retry_msg)
    return return_val
