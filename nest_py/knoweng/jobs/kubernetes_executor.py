"""This module defines constants and a base class for knoweng analytics jobs
   that run remotely on Kubernetes.

   This module will only be called when the EXEC_MODE environment variable
   has been configured with a value of "kubernetes"

   Supports the following environment configurations:

   Variable Name              (Default Value)
   ------------------------------------------------
   - NEST_RUNLEVEL            ('development')
   - TOKEN_FILE_PATH          ('/var/run/secrets/kubernetes.io/serviceaccount/token')
   - NODE_LABEL_NAME          ('kops.k8s.io/instancegroup')
   - NODE_LABEL_VALUE         ('nodes')
   - AWS_SHARED_MNT_PATH      ('')
   - KUBERNETES_SERVICE_HOST  ('10.0.0.1')
   - KUBERNETES_SERVICE_PORT  (443)
   - AWS_REDIS_HOST           ('redis')
   - AWS_REDIS_PORT           (6379)
   - AWS_REDIS_PASS           ('GARBAGESECRET')
"""

import json
import logging
import os
from time import sleep
from nest_py.knoweng.jobs.abstract_executor import AbstractExecutor, \
    is_response_ok, retry_request_until_ok

import requests

LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.INFO)

NEST_RUNLEVEL = os.getenv('NEST_RUNLEVEL', 'development')

# Read Kubernetes auth token from the ServiceAccount file on disk
# TODO how to adjust for multiple clouds?
token_file_path = os.getenv(\
    'TOKEN_FILE_PATH', '/var/run/secrets/kubernetes.io/serviceaccount/token')
token_file = open(token_file_path, 'r')
auth_token = token_file.read()
default_headers = {
    'Content-Type': 'application/json',
    'Authorization': 'Bearer ' + auth_token
}
token_file.close()

class KubernetesExecutor(AbstractExecutor):
    """Base class for analytics jobs that run remotely via Kubernetes."""

    # The name of the label under which to schedule these jobs
    kops_label_name = os.getenv('NODE_LABEL_NAME', 'kops.k8s.io/instancegroup')
    kops_label_value = os.getenv('NODE_LABEL_VALUE', 'pipes')
    hostpath_shared_mnt = os.getenv('AWS_SHARED_MNT_PATH', '')

    # TODO move into config
    # FIXME: this may not work across namespaces... detect via DNS instead?
    cloud_master_dict = {
        # Use the service discovery environment variables created by k8s
        # See https://kubernetes.io/docs/concepts/services-networking/service/#environment-variables
        'aws': os.getenv('KUBERNETES_SERVICE_HOST', '10.0.0.1') + ':' + \
                str(os.getenv('KUBERNETES_SERVICE_PORT', 443))
    }
    """Map from cloud name to Kubernetes apiserver."""

    # TODO move into config
    cloud_path_dict = {
        'aws': '/'
    }
    """Map from cloud name to container mount path."""

    def __init__(self, job_name, timeout, cloud, docker_image, \
        num_cpus, max_ram_mb):
        """Initializes self.

        Args:
            job_name (str): A name to identify the job in Kubernetes.
            timeout (int): The maximum execution time in seconds.
            cloud (str): The cloud name, which must appear as a key in
                cloud_path_dict.
            docker_image (str): The docker image name for Kubernetes to run.
            num_cpus (int): The number of CPUs to allocate for the job. Note
                AWS m4.xl is 4 CPUs.
            max_ram_mb (int): The maximum RAM in megabytes to allocate for the
                job. Note AWS m4.xl is 16 GB.

        Returns:
            None: None.

        """
        LOGGER.debug('KubernetesExecutor.__init__')
        self.job_name = job_name
        self.timeout = timeout
        self.cloud = cloud
        self.docker_image = docker_image
        self.num_cpus = num_cpus
        self.max_ram_mb = max_ram_mb

        # Resource limits / requests have been chosen such that all pipelines
        # can run in both development (single-node)
        # or production (multi-node) environments

        # CPU is measured in microns (m) or integers, where 1000m = 1 CPU
        # RAM is measured in MB (M) or GB (G)

        # Assume that this value is in MB
        self.limits_ram = self.max_ram_mb

        # Assume that this value is in microns
        self.limits_cpu = 1000 * self.num_cpus

        # Increase the resources requested for production pipelines
        # FIXME: This is what caused the outOfCpu problem during the demo
        #if NEST_RUNLEVEL == 'production':
        #    self.requests_ram = 3500
        #    self.requests_cpu = 1000
        #else:
        self.requests_ram = 2500
        self.requests_cpu = 700

        if self.requests_ram > self.limits_ram:
            err_message = 'Invalid resources: requested memory (' + \
                str(self.requests_ram) + ') may ' + \
                'not exceed memory limit (' + str(self.limits_ram) + ')'
            LOGGER.error(err_message)
            raise ValueError(err_message)

        if self.requests_cpu > self.limits_cpu:
            err_message = 'Invalid resources: requested CPU may (' + \
                str(self.requests_cpu) + ') not exceed CPU limit (' + \
                self.limits_cpu +')'
            LOGGER.error(err_message)
            raise ValueError(err_message)


    def start(self, command):
        """Submits the job to Kubernetes. Runs command in the remote docker
        container.

        Args:
            command (str): The command to run inside the container.

        Returns:
            None: None.

        """
        LOGGER.debug('KubernetesExecutor.start')

        # Build up a JSON spec to submit to Kubernetes
        # TODO: refactor - extract method
        payload = {
            "apiVersion": "batch/v1",
            "kind": "Job",
            "metadata": {"name": self.job_name},
            "spec": {
                # FIXME: due to k8s bug, not currently
                # working when restartPolicy=OnFailure)
                # "backoffLimit": 5,  # failure threshold

                "activeDeadlineSeconds": self.timeout,
                "template": {
                    "metadata": {"name": self.job_name},
                    "spec": {
                        "restartPolicy": "OnFailure",
                        "containers": [
                            {
                                "name": self.job_name, # This could be pipeline_slug?
                                "image": self.docker_image,
                                "imagePullPolicy": "Always",
                                "command": ["bash"],
                                "args": ["-c", command],
                                "resources": {
                                    "requests": {
                                        "cpu": str(self.requests_cpu) + 'm',
                                        "memory": str(self.requests_ram) + 'M'
                                    },
                                    "limits": {
                                        "cpu": str(self.limits_cpu) + 'm',
                                        "memory": str(self.limits_ram) + "M"
                                    }
                                },
                                "volumeMounts": [
                                    # All PipelineJobs require the userfiles to be present
                                    {
                                        "name": "userfiles",
                                        "mountPath": "/userfiles"
                                    },
                                    # GSC only: /networks must be populated
                                    {
                                        "name": "networks",
                                        "mountPath": "/networks"
                                    }
                                ]
                            }
                        ],
                        # FIXME: switch on NEST_RUNLEVEL for hostPath vs EFS?
                        "volumes": [
                            {
                                "name": "userfiles",
                                "hostPath": {"path": KubernetesExecutor.hostpath_shared_mnt + '/userfiles'}
                            },
                            {
                                "name": "networks",
                                "hostPath": {"path": KubernetesExecutor.hostpath_shared_mnt + '/networks'}
                            }
                        ],
                        # to ensure only pipeline jobs can run on the autoscaling
                        # instance group, which has a matching taint
                        "tolerations": [
                            {
                                "key": "dedicated",
                                "operator": "Equal",
                                "value": "pipelines_jobs",
                                "effect": "NoSchedule"
                            }
                        ]
                    }
                }
            }
        }

        # If this is production, adjust payload before submitting
        if NEST_RUNLEVEL == 'production':
            # IMPORTANT: adjust volumes to mount from EFS instead of hostPath
            # These EFS PVCs must exist in Kubernetes, and /networks will need
            # to be populated from the current contents of the networks shared mount
            efs_volumes = []
            for vol in payload['spec']['template']['spec']['volumes']:
                vol_name = vol['name']
                efs_vol = {
                    "name": vol_name,
                    "persistentVolumeClaim": {"claimName": "efs-" + vol_name}
                }
                LOGGER.info('Converted to EFS volume: ' + json.dumps(efs_vol))
                efs_volumes.append(efs_vol)

            payload['spec']['template']['spec']['volumes'] = efs_volumes

            # Optional: Add a nodeSelector to schedule these jobs in
            # the "pipes" auto-scaling instance group on AWS
            payload['spec']['template']['spec']['nodeSelector'] = {}
            payload['spec']['template']['spec']['nodeSelector'][KubernetesExecutor.kops_label_name] = \
                KubernetesExecutor.kops_label_value

            LOGGER.info('Production job payload: ' + json.dumps(payload))

        # submit to Kubernetes
        LOGGER.debug('>>> Submitting payload: ' + json.dumps(payload))
        LOGGER.info('Starting ' + self.job_name + '...')
        master_host = 'https://' + \
            KubernetesExecutor.cloud_master_dict[self.cloud] + \
            '/apis/batch/v1/namespaces/default/jobs'
        response = requests.post(master_host, json=payload, \
            headers=default_headers, verify=False)
        is_response_ok(response, 1, -1)

    def is_running(self):
        """Returns True if the job is running, else False.

        Returns:
            boolean: True if the job is running, else False.

        """
        LOGGER.debug('KubernetesExecutor.is_running')

        url = 'https://' + KubernetesExecutor.cloud_master_dict[self.cloud] + \
            '/apis/batch/v1/namespaces/default/jobs/' + self.job_name

        LOGGER.debug('Checking that job exists: ' + url)
        response = requests.get(url, headers=default_headers, verify=False)
        ok = is_response_ok(response, 1, -1)
        # If no exception was raised, our request returned a response
        return ok

    def is_failed(self):
        """Returns True if the job has failed, else returns False.

        Returns:
            boolean: True if the job has failed, else False.

        """
        # TODO: Reach out to Kubernetes API to check job status
        LOGGER.debug('KubernetesExecutor.is_failed')

        url = 'https://' + KubernetesExecutor.cloud_master_dict[self.cloud] + \
                '/apis/batch/v1/namespaces/default/jobs/' + self.job_name
        LOGGER.debug('Getting job status from ' + url)
        request_lambda = lambda: requests.get(\
            url, headers=default_headers, verify=False)
        k8s_response = retry_request_until_ok(request_lambda, 1, 2)
        return_val = False
        if k8s_response is not None:
            json_resp = json.loads(k8s_response.text)
            LOGGER.debug('>>> Got response: ' + k8s_response.text)
            status = json_resp['status']
            if 'conditions' in status:
                conditions = status['conditions']
                for condition in conditions:
                    if 'type' in condition and condition['type'] == "Failed":
                        return_val = condition['status'] == 'True'
                        LOGGER.debug(self.job_name + ' is failed? ' + \
                            str(return_val))
            else:
                LOGGER.debug('No job status conditions found: ' + \
                    str(return_val))
        return return_val

    def get_error_message(self):
        """Returns the error message if this job has failed, else returns None.

        Returns:
            str: The error message if this job has failed, else None.

        """
        # Reach out to Kubernetes API to retrieve job logs
        # TODO: this has not been tested very thoroughly

        LOGGER.debug('KubernetesExecutor.get_error_message')
        LOGGER.debug(' >>> Reading error message for: ' + self.job_name)

        # Look up the pod_name for this job
        pods_url = 'https://' + \
            KubernetesExecutor.cloud_master_dict[self.cloud] + \
            '/api/v1/namespaces/default/pods?labelSelector=job-name%3D' + \
            self.job_name

        LOGGER.debug('Getting pod name from ' + pods_url)
        request_lambda = lambda: requests.get(\
            pods_url, headers=default_headers, verify=False)
        k8s_response = retry_request_until_ok(request_lambda, 3, 10)
        return_val = "Error reading logs"
        if k8s_response is not None:
            job_pod = k8s_response.json()
            pod_name = job_pod['metadata']['name']
            LOGGER.debug('>>> Got pod name: ' + pod_name)

            # Then read and return the logs from that pod
            logs_url = 'https://' + \
                KubernetesExecutor.cloud_master_dict[self.cloud] + \
                '/api/v1/namespaces/default/pods/' + pod_name + '/log'

            LOGGER.debug('Getting logs from ' + logs_url)
            request_lambda2 = lambda: requests.get(\
                logs_url, headers=default_headers, verify=False)
            k8s_response2 = retry_request_until_ok(request_lambda2, 3, 10)
            if k8s_response2 is not None:
                return_val = k8s_response2.text
                LOGGER.debug('Got logs: ' + return_val)
        return return_val

    def is_done(self):
        """Returns True if the job is done, else returns False. TODO confirm
        behavior if done but deleted.

        Returns:
            boolean: True if the job is done, else False.

        """
        LOGGER.debug('KubernetesExecutor.is_done')

        url = 'https://' + KubernetesExecutor.cloud_master_dict[self.cloud] + \
            '/apis/batch/v1/namespaces/default/jobs/' + self.job_name

        LOGGER.debug('Getting job status from ' + url)
        request_lambda = lambda: requests.get(\
            url, headers=default_headers, verify=False)
        k8s_response = retry_request_until_ok(request_lambda, 1, 0)
        return_val = False
        if k8s_response is not None:
            json_resp = json.loads(k8s_response.text)
            LOGGER.debug('>>> Got response: ' + k8s_response.text)
            status = json_resp['status']
            if 'conditions' in status:
                conditions = status['conditions']
                for condition in conditions:
                    if 'type' in condition and condition['type'] == "Complete":
                        return_val = condition['status'] == 'True'
                        LOGGER.debug(self.job_name + ' is done? ' + \
                            str(return_val))
            else:
                LOGGER.debug('No job status conditions found: ' + str(return_val))
        return return_val

    def delete(self):
        """Deletes the job from Kubernetes. Note that while `kubectl delete job`
        will also clean up the remaining pods, the REST API apparently does not
        share this behavior. So we make a few extra REST calls to scale down and
        clean up any leftover pod resources.

        Returns:
            None: None.

        """
        k8s_hostname = 'https://' + \
            KubernetesExecutor.cloud_master_dict[self.cloud]
        jobs_url = k8s_hostname + '/apis/batch/v1/namespaces/default/jobs/' + \
            self.job_name

        # Get current Job object to scale it down
        LOGGER.debug('Removing orphaned job pods for ' + str(self.job_name))
        jobs_get_response = requests.get(\
            jobs_url, headers=default_headers, verify=False)
        ok = is_response_ok(jobs_get_response, 1, -1)
        if ok:
            # Scale current number of Pods for the Job down to zero
            job_json = jobs_get_response.json()
            job_json['spec']['parallelism'] = 0
            LOGGER.debug('Changing job parallelism to zero...')
            jobs_put_response = requests.put(jobs_url, data=json.dumps(job_json), \
                headers=default_headers, verify=False)
            ok = is_response_ok(jobs_put_response, 1, -1)
        if ok:
            # Check for any leftover pod replicas
            LOGGER.debug('Looking up job uid: ' + str(self.job_name))
            job_controller_uid = job_json['metadata']['labels']['controller-uid']

            # NOTE: "%3D" is a URL-encoded equal sign ("=")
            pod_list_url = k8s_hostname + '/api/v1/namespaces/default/pods?' + \
                'labelSelector=controller-uid%3D' + str(job_controller_uid)

            continue_deleting = True
            while continue_deleting:
                pod_list_response = requests.get(\
                    pod_list_url, headers=default_headers, verify=False)
                ok = is_response_ok(pod_list_response, 1, -1)

                orphaned_pod_list = pod_list_response.json()
                LOGGER.debug('Checking for orphaned job pods for: ' + \
                    str(self.job_name))
                if not orphaned_pod_list['items']:
                    LOGGER.info('All pods removed for job: ' + \
                        str(self.job_name))
                    continue_deleting = False
                else:
                    LOGGER.debug('Orphaned pod found!')
                    orphan_pod = orphaned_pod_list['items'][0]
                    pod_name = orphan_pod['metadata']['name']
                    LOGGER.debug('Deleting orphaned pod: ' + str(pod_name))
                    pod_delete_url = k8s_hostname + \
                        '/api/v1/namespaces/default/pods/' + pod_name
                    pod_delete_response = requests.delete(pod_delete_url, \
                        headers=default_headers, verify=False)
                    if is_response_ok(pod_delete_response, 1, -1):
                        LOGGER.debug('Pod deleted: ' + str(pod_name))

                if continue_deleting:
                    sleep(1)

            # Then delete the Job itself
            LOGGER.debug('Deleting job: ' + self.job_name)
            job_delete_response = requests.delete(jobs_url, \
                headers=default_headers, verify=False)
            ok = is_response_ok(job_delete_response, 1, -1)

            LOGGER.debug('Job successfully deleted!')

    @staticmethod
    def get_all_job_names(cloud):
        """Returns all job names known to Kubernetes.

        Args:
            cloud (str): The cloud name, which must appear as a key in
                cloud_path_dict.

        Returns:
            list(str): A list of job names.

        """
        url = 'https://' + KubernetesExecutor.cloud_master_dict[cloud] + \
            '/apis/batch/v1/namespaces/default/jobs'
        LOGGER.debug('Getting all job names from ' + url)
        return_val = []
        request_lambda = lambda: requests.get(\
            url, headers=default_headers, verify=False)
        k8s_response = retry_request_until_ok(request_lambda, 1, 0)
        if k8s_response is not None:
            return_val = [job['name'] for job in k8s_response.json()]
        return return_val
