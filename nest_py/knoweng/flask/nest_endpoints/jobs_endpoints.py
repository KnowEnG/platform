"""This module defines a set of hooks for the job endpoint.
"""
import pickle
from werkzeug.exceptions import UnsupportedMediaType

from redis import Redis
import rq.job as rqjob
from rq import Queue
import flask

from nest_py.core.flask.nest_endpoints.crud_endpoints import NestCrudEntryEndpoint
from nest_py.core.flask.nest_endpoints.crud_endpoints import NestCrudCollectionEndpoint
from nest_py.core.flask.nest_endpoints.nest_endpoint_set import NestEndpointSet
from nest_py.core.data_types.nest_date import NestDate

import nest_py.knoweng.data_types.jobs as jobs

def get_endpoint_set(jobs_db_client, authenticator):
    rel_url = jobs.COLLECTION_NAME
    api_transcoder = jobs.generate_schema()

    collection_ep = JobsCollectionEndpoint(rel_url, jobs_db_client, \
        api_transcoder, authenticator)
    entry_ep = JobsEntryEndpoint(rel_url, jobs_db_client, \
        api_transcoder, authenticator)

    eps = NestEndpointSet()
    eps.add_endpoint(collection_ep)
    eps.add_endpoint(entry_ep)
    return eps

class JobsEntryEndpoint(NestCrudEntryEndpoint):

    def do_PATCH(self, request, requesting_user, nid_int):
        """
        adds an 'updated' timestamp to the incoming
        request (based on the localhost time) before
        doing a normal update
        """
        nest_date_jdata = NestDate.now().to_jdata()
        request.json['_updated'] = nest_date_jdata
        res = super(JobsEntryEndpoint, self).do_PATCH(request, \
            requesting_user, nid_int)
        return res


class JobsCollectionEndpoint(NestCrudCollectionEndpoint):
    """Provides special side effects for kicking off a job
    when the job's db entry is posted through do_POST"""

    def __init__(self, rel_url, crud_db_client, api_transcoder, authenticator):

        super(JobsCollectionEndpoint, self).__init__(
            rel_url, crud_db_client, api_transcoder, authenticator)

        self.userfiles_dir = None
        """The path to a directory that contains any user files stored on disk."""

        self.rq_job_queue = None
        """The job queue."""

        self._init_resources()
        return

    def _init_resources(self):
        config = flask.current_app.config
        self.userfiles_dir = config['USERFILES_DIR']
        redis_connection = Redis(\
            host=config['REDIS_HOST'], db=config['JOB_QUEUE_REDIS_DB'])
        self.rq_job_queue = Queue(\
            config['JOB_QUEUE_DEFAULT_NAME'], connection=redis_connection)
        # RQ's job module prefers cPickle to pickle if the former is available
        # jython does implement cPickle, but because it's a built-in module
        # (not standard library), total compatibility isn't guaranteed
        # the problem for us is jython's impl doesn't support keyword args
        # this line ensures we use plain old pickle
        rqjob.dumps = pickle.dumps

        return

    def do_POST(self, request, requesting_user, **kwargs):
        """Add job status to incoming object.

        Args:
            request (flask.request): The request object.
        """
        # need to set the job status to running
        content_type = request.headers['Content-Type']
        if 'application/x-www-form-urlencoded' in content_type or \
            'multipart/form-data' in content_type:
            jdata = request.form.to_dict()
        elif 'application/json' in content_type:
            jdata = dict(request.json)
        else:
            raise UnsupportedMediaType(\
                'expected application/x-www-form-urlencoded, ' + \
                'multipart/form-data, or application/json Content-Type; ' + \
                'got ' + request.headers['Content-Type'])

        nest_date_jdata = NestDate.now().to_jdata()
        jdata['_created'] = nest_date_jdata
        jdata['_updated'] = nest_date_jdata
        jdata['status'] = 'running'
        if 'error' not in jdata:
            jdata['error'] = None

        # enforce limits:
        # 1. no more than MAX_JOBS_TOTAL_PER_USER
        max_total = \
            flask.current_app.config['MAX_JOBS_TOTAL_PER_USER']
        # 2. no more than MAX_JOBS_RUNNING_PER_USER
        max_running = \
            flask.current_app.config['MAX_JOBS_RUNNING_PER_USER']
        job_tles = self.crud_client.simple_filter_query(\
            dict(), user=requesting_user)
        current_running = len(\
            [jt for jt in job_tles if jt.get_value('status') == 'running'])
        if len(job_tles) > max_total:
            resp = self._make_error_response('Your total number of jobs ' + \
                'exceeds ' + str(max_total) + '. Make room for new jobs by ' + \
                'deleting previous jobs, or contact us for a premium account.')
        elif current_running > max_running:
            resp = self._make_error_response('You already have ' + \
                str(current_running) + ' jobs running. Wait for a job to ' + \
                'finish before starting this one, or contact us for a ' + \
                'premium account')
        else:
            job_tle = self.transcoder.jdata_to_object(jdata)
            job_tle = self.crud_client.create_entry(job_tle, user=requesting_user)
            if job_tle is None:
                resp = self._make_error_response('Failed to write job to DB')
            else:
                jdata = self.format_create_single_jdata(request, job_tle)
                resp = self._make_success_json_response(jdata)
                # passing the job function as a string prevents the python runtime
                # in the flask process from importing everything on the job queue
                # side of the house
                job_id = job_tle.get_nest_id()
                self.rq_job_queue.enqueue_call(\
                    func='nest_py.knoweng.jobs.worker_app.run_job', \
                    args=(requesting_user, job_id), \
                    timeout=1200)
        return resp
