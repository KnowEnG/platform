"""
This module defines the rq worker methods.
"""
import multiprocessing
from time import sleep
from redis import Redis
from rq import Queue, Connection, Worker, get_current_job

import nest_py.core.nest_config as nest_config
from nest_py.core.data_types.nest_id import NestId
import nest_py.knoweng.data_types.projects as projects
from nest_py.knoweng.jobs.db_utils import init_token_maker, init_crud_clients, get_job_record, update_job_record
from nest_py.knoweng.jobs.gene_prioritization import get_gene_prioritization_runners
from nest_py.knoweng.jobs.gene_set_characterization import get_gene_set_characterization_runners
from nest_py.knoweng.jobs.sample_clustering import get_sample_clustering_runners

#TODO: move the needed config out of 'nest_config'.
CONFIG = nest_config.generate_config_from_os()
USERFILES_DIR = CONFIG['USERFILES_DIR']

def run_job(nest_user, job_id):
    """Runs a job in the job queue.

    nest_user (NestUser) running the job on behalf of
    job_id (NestId) id of the job entry in the DB

    FIXME job_id is currently args[1], and handle_error below expects to find
    it there. Don't change the parameter list above without changing
    handle_error to match.

    """
    # FIXME just handling knoweng for now
    # FIXME adding very simple support for execution of multiple chronos jobs
    # constituting one nest job. ultimately want this handled within chronos
    # or on the other side of chronos
    # lots of room for improvement
    runners = []
    print "Begin worker_app.run_job"

    user_id = nest_user.get_nest_id()
    print 'user_id: ' + str(user_id) + ' job_id: ' + str(job_id)
    job_tle = get_job_record(user_id, job_id)
    job_data = job_tle.get_data_dict()
    pipeline = job_data['pipeline']
    parameters = job_data['parameters']
    project_id = job_data['project_id']
    rel_project_dir = projects.project_dirpath('.', project_id)

    timeout = get_current_job().timeout
    if pipeline == 'sample_clustering':
        if 'response_file' in parameters and parameters['response_file'] is not None:
            response_file_id = NestId(int(parameters['response_file']))
        else:
            response_file_id = None
        runners = get_sample_clustering_runners(\
            user_id, job_id, USERFILES_DIR, rel_project_dir, timeout,
            parameters.get('cloud'), parameters.get('species'),
            NestId(int(parameters.get('features_file'))),
            response_file_id,
            parameters.get('method'),
            int(parameters.get('num_clusters')),
            parameters.get('use_network'),
            parameters.get('network_name'),
            float(parameters.get('network_smoothing', 0)),
            parameters.get('use_bootstrapping'),
            int(parameters.get('num_bootstraps', 0)),
            float(parameters.get('bootstrap_sample_percent', 0)))
    elif pipeline == 'gene_set_characterization':
        runners = get_gene_set_characterization_runners(\
            user_id, job_id, USERFILES_DIR, rel_project_dir, timeout,
            parameters.get('cloud'), parameters.get('species'),
            NestId(int(parameters['gene_set_file'])),
            parameters.get('gene_collections'),
            parameters.get('method'), parameters.get('network_name'),
            float(parameters.get('network_smoothing', 0)))
    elif pipeline == 'gene_prioritization':
        runners = get_gene_prioritization_runners(\
            user_id, job_id, USERFILES_DIR, rel_project_dir, timeout,
            parameters.get('cloud'), parameters.get('species'),
            NestId(int(parameters.get('features_file'))),
            NestId(int(parameters.get('response_file'))),
            parameters.get('correlation_method'),
            parameters.get('use_network'),
            parameters.get('network_name'),
            float(parameters.get('network_influence', 0)),
            int(parameters.get('num_response_correlated_genes', 0)),
            parameters.get('use_bootstrapping'),
            int(parameters.get('num_bootstraps', 0)),
            float(parameters.get('bootstrap_sample_percent', 0)))
    elif pipeline == 'spreadsheet_visualization':
        # TODO: Support multiple file selection (array of "secondary" files?)
        if 'secondary_files' in parameters and parameters['secondary_files'] is not None:
            response_file_id = NestId(int(parameters['secondary_files']))
        else:
            response_file_id = None
        
        # Just run sample_clustering for now, with hardcoded defaults for missing parameters
        # TODO: Update this if/when a new Docker image is created for SSV
        runners = get_sample_clustering_runners(\
            user_id, job_id, USERFILES_DIR, rel_project_dir, timeout,
            parameters.get('cloud', 'aws'), parameters.get('species', '9606'),
            NestId(int(parameters.get('primary_file'))),
            response_file_id,
            parameters.get('method', 'K-means'),
            int(parameters.get('num_clusters', '5')),
            parameters.get('use_network', False),
            parameters.get('network_name', 'STRING_experimental'),
            float(parameters.get('network_smoothing', '50')),
            parameters.get('use_bootstrapping', False),
            int(parameters.get('num_bootstraps', '8')),
            float(parameters.get('bootstrap_sample_percent', '80')))
    elif pipeline == 'phenotype_prediction':
        pass
    else:
        raise ValueError('Unknown technique ' + pipeline)

    # execute
    error_message = None
    while runners:
        # first check for errors
        failed = [r for r in runners if r.is_failed()]
        if failed:
            error_message = ' '.join([f.get_error_message() for f in failed])
            runners = None
        else:
            # next remove and process anything done. note a job can be done
            # before # it's even started, in the case that the same
            # configuration was # previously run as another job and the results
            # are found on disk
            done = [r for r in runners if r.is_done()]
            for runner in done:
                runner.on_done()
            # remove according to membership in done list, not by
            # calling is_done() again, in case status changed since we last
            # checked
            runners = [r for r in runners if r not in done]
            # now start anything ready
            ready = [r for r in runners if r.is_ready() and not r.is_started()]
            for runner in ready:
                runner.start()
            if runners:
                sleep(2) # sleep two seconds

    # record status
    # TODO reconsider once new data endpoints are ready
    if error_message is None:
        update_job_record(user_id, job_id, {'status': 'completed'})
    else:
        update_job_record(user_id, job_id, \
            {'status': 'failed', 'error': error_message})

def handle_error(job, ex_type, ex_value, traceback):
    """
    Handles any exception in a running job by updating the job status in the db.

    Arguments:
        job (rq.Job): the current job
        ex_type (class): the exception type
        ex_value (Exception): the exception objet
        traceback (traceback): the exception traceback
    """
    # RQ already logs the error for us
    nest_user = job.args[0]
    user_id = nest_user.get_nest_id()
    job_id = job.args[1]
    if job_id:
        update_job_record(user_id, job_id, \
            {
                'status': 'failed',
                'error': 'Unknown error: ' + str(ex_value)
            })

def main():
    """Starts the RQ worker."""

    init_token_maker(CONFIG['JWT_SECRET'], CONFIG['JWT_ISSUER'], \
        CONFIG['JWT_AUDIENCES'])
    init_crud_clients()

    with Connection(Redis(\
            host=CONFIG['REDIS_HOST'], db=CONFIG['JOB_QUEUE_REDIS_DB'])):
        # provide queue names to monitor
        queues = [Queue(CONFIG['JOB_QUEUE_DEFAULT_NAME'])]

        workers = []
        for i in range(CONFIG['JOB_QUEUE_WORKERS']):
            p = multiprocessing.Process(target=Worker(queues, exception_handlers=[handle_error]).work)
            workers.append(p)
            p.start()

if __name__ == '__main__':
    main()
