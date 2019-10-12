"""This module is to disable single PATCH, POST on ssv related endpoints
"""
import pickle
import time

import flask
from redis import Redis
from rq import Queue
import rq.job as rqjob

from nest_py.core.flask.nest_endpoints.nest_endpoint import NestEndpoint
from nest_py.core.flask.nest_endpoints.nest_endpoint_set import NestEndpointSet
from nest_py.core.flask.nest_endpoints.crud_endpoints import NestCrudEntryEndpoint
from nest_py.core.flask.nest_endpoints.crud_endpoints import NestCrudCollectionEndpoint

def generate_endpoints(ssviz_schema, crud_db_client, authenticator):
    endpoint_set = NestEndpointSet()
    transcoder = ssviz_schema
    relative_url_base = ssviz_schema.get_name()
    epc = SsvizCollectionEndpoint(relative_url_base, \
        crud_db_client, transcoder, authenticator)
    endpoint_set.add_endpoint(epc)

    epe = SsvizCrudEntryEndpoint(relative_url_base, crud_db_client, \
        transcoder, authenticator)
    endpoint_set.add_endpoint(epe)
    return endpoint_set

class SsvizCrudEntryEndpoint(NestCrudEntryEndpoint):

    def do_PATCH(self, request, requesting_user, nid_int):
        payload = "PATCH not supported at this endpoint"
        resp = flask.make_response(payload, 405)
        return resp

class SsvizCollectionEndpoint(NestCrudCollectionEndpoint):

    def do_POST(self, request, requesting_user, **kwargs):
        payload = "POST not supported at this endpoint"
        resp = flask.make_response(payload, 405)
        return resp

class SsvizSurvivalAnalysesEndpoint(NestEndpoint):

    def __init__(self, authenticator):
        """
        """
        super(SsvizSurvivalAnalysesEndpoint, self).__init__(\
            'ssviz_survival_analyses', authenticator)

        self.rq_job_queue = None
        """The job queue."""

        self._init_resources()

    def _init_resources(self):
        config = flask.current_app.config
        redis_connection = Redis(\
            host=config['REDIS_HOST'], db=config['JOB_QUEUE_REDIS_DB'])
        self.rq_job_queue = Queue(\
            config['JOB_QUEUE_DEFAULT_NAME'], connection=redis_connection)
        # see comment in jobs_endpoint
        rqjob.dumps = pickle.dumps

    def get_flask_rule(self):
        rule = 'ssviz_survival_analyses'
        return rule

    def get_flask_endpoint(self):
        return 'ssviz_survival_analyses'

    def do_GET(self, request, requesting_user):
        # unpack params from MultiDict
        flat_params = {k: v for k, v in request.args.iteritems(multi=False)}
        timeout_secs = 30
        remote_job = self.rq_job_queue.enqueue_call(\
            func='nest_py.knoweng.jobs.worker_app.run_calculation', \
            args=(requesting_user, 'ssviz_survival_analysis', flat_params), \
            timeout=timeout_secs)
        # monitor the job until it's done
        start_time = time.time()
        status = None
        resp = None
        while True:
            status = remote_job.get_status()
            if status == 'finished':
                resp = self._make_success_json_response({'pval': \
                    remote_job.result})
                break
            elif status == 'failed' or time.time() - start_time > timeout_secs:
                resp = self._make_error_response(\
                    'Calculation failed with status ' + str(status))
                break
            time.sleep(1)
        return resp
