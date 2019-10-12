"""
This module defines the rq worker methods.
"""
import multiprocessing
import logging
from time import sleep
import os

from redis import Redis
from rq import Queue, Connection, Worker, get_current_job

import nest_py.core.nest_config as nest_config
from nest_py.core.data_types.nest_id import NestId
import nest_py.knoweng.data_types.projects as projects
from nest_py.knoweng.jobs.db_utils import init_token_maker, init_crud_clients,\
    get_job_record, update_job_record
import nest_py.knoweng.jobs.knoweng_seed_job as knoweng_seed_job

from nest_py.knoweng.jobs.pipelines.feature_prioritization import \
    get_feature_prioritization_runners
from nest_py.knoweng.jobs.pipelines.gene_set_characterization import \
    get_gene_set_characterization_runners
from nest_py.knoweng.jobs.pipelines.sample_clustering import \
    get_sample_clustering_runners
from nest_py.knoweng.jobs.pipelines.signature_analysis import \
    get_signature_analysis_runners
from nest_py.knoweng.jobs.pipelines.spreadsheet_visualization import \
    get_spreadsheet_visualization_runners, calculate_survival_pval

#TODO: move the needed config out of 'nest_config'.
CONFIG = nest_config.generate_config_from_os()
USERFILES_DIR = CONFIG['USERFILES_DIR']
logging.basicConfig()
LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.INFO)

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
    LOGGER.info("Begin worker_app.run_job")

    user_id = nest_user.get_nest_id()
    LOGGER.info('user_id: ' + str(user_id) + ' job_id: ' + str(job_id))
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
            user_id, job_id, project_id, USERFILES_DIR, rel_project_dir, timeout,
            parameters.get('cloud'), parameters.get('species'),
            NestId(int(parameters.get('features_file'))),
            response_file_id,
            int(parameters.get('num_clusters')),
            parameters.get('method'),
            parameters.get('affinity_metric', None),
            parameters.get('linkage_criterion', None),
            int(parameters.get('num_nearest_neighbors', 0)),
            parameters.get('use_network'),
            parameters.get('network_name'),
            float(parameters.get('network_smoothing', 0)),
            parameters.get('use_bootstrapping'),
            int(parameters.get('num_bootstraps', 0)),
            float(parameters.get('bootstrap_sample_percent', 0)))
    elif pipeline == 'gene_set_characterization':
        runners = get_gene_set_characterization_runners(\
            user_id, job_id, project_id, USERFILES_DIR, rel_project_dir, timeout,
            parameters.get('cloud'), parameters.get('species'),
            NestId(int(parameters['gene_set_file'])),
            parameters.get('gene_collections'),
            parameters.get('method'), parameters.get('network_name'),
            float(parameters.get('network_smoothing', 0)))
    elif pipeline == 'feature_prioritization':
        runners = get_feature_prioritization_runners(\
            user_id, job_id, project_id, USERFILES_DIR, rel_project_dir, timeout,
            parameters.get('cloud'), parameters.get('species'),
            NestId(int(parameters.get('features_file'))),
            NestId(int(parameters.get('response_file'))),
            parameters.get('correlation_method'),
            parameters.get('missing_values_method'),
            parameters.get('use_network'),
            parameters.get('network_name'),
            float(parameters.get('network_influence', 0)),
            int(parameters.get('num_response_correlated_features', 0)),
            int(parameters.get('num_exported_features', 0)),
            parameters.get('use_bootstrapping'),
            int(parameters.get('num_bootstraps', 0)),
            float(parameters.get('bootstrap_sample_percent', 0)))
    elif pipeline == 'signature_analysis':
        runners = get_signature_analysis_runners(\
            user_id, job_id, project_id, USERFILES_DIR, rel_project_dir, timeout,
            parameters.get('cloud'),
            NestId(int(parameters.get('query_file'))),
            NestId(int(parameters.get('signatures_file'))),
            parameters.get('similarity_measure'))
    elif pipeline == 'spreadsheet_visualization':
        spreadsheet_nest_ids = []
        if 'spreadsheets' in parameters and parameters['spreadsheets'] is not None:
            file_ids = parameters['spreadsheets'].split(',')
            spreadsheet_nest_ids = [NestId(int(fid)) for fid in file_ids]
        runners = get_spreadsheet_visualization_runners(\
            user_id, job_id, project_id, USERFILES_DIR, rel_project_dir,
            spreadsheet_nest_ids)
    elif pipeline == 'phenotype_prediction':
        pass
    else:
        raise ValueError('Unknown technique ' + pipeline)

    # execute
    error_message = None
    while runners:
        LOGGER.debug('Looping...')
        # first check for errors
        failed = [r for r in runners if r.is_failed()]
        if failed:
            # Read the error message from the failed job
            error_message = ' '.join([f.get_error_message() for f in failed])
            # Delete job record
            # we can delete all items in runners, because they're all part of
            # the same parent job, and we're declaring the entire job a failure
            for runner in runners:
                LOGGER.warning('Cleaning up after failure: ' + runner.job_name)
                try:
                    # note locally executed jobs don't define this method
                    # apparently try/except is the pythonic and performant way
                    # to check
                    # TODO either eliminate locally executed jobs or else
                    # unify
                    runner.delete_job_record()
                except AttributeError:
                    # no such method
                    LOGGER.warning("Don't know how to delete " + \
                        runner.job_name + " after failure.")
            # Then end the job loop
            runners = None
            LOGGER.error(' >>>>>> ERROR: ' + error_message)
        else:
            # next remove and process anything done. note a job can be done
            # before # it's even started, in the case that the same
            # configuration was # previously run as another job and the results
            # are found on disk
            done = [r for r in runners if r.is_done()]
            for runner in done:
                LOGGER.info('Marking runner for ' + runner.job_name + ' as done...')
                runner.on_done()
            LOGGER.debug('Done runners for ' + runners[0].job_name + ': ' + \
                str(len(done)))
            # remove according to membership in done list, not by
            # calling is_done() again, in case status changed since we last
            # checked
            runners = [r for r in runners if r not in done]
            # now start anything ready
            ready = [r for r in runners if r.is_ready() and not r.is_started()]
            for runner in ready:
                runner.start()
            if runners:
                LOGGER.debug('Runners left in queue: ' + str(runners))
                sleep(5) # sleep five seconds

    # record status
    # TODO reconsider once new data endpoints are ready
    if error_message is None:
        update_job_record(user_id, job_id, {'status': 'completed'})
    else:
        update_job_record(user_id, job_id, \
            {'status': 'failed', 'error': error_message})

def run_calculation(nest_user, calculation_name, params):
    return_val = None
    if calculation_name == 'ssviz_survival_analysis':
        return_val = calculate_survival_pval(\
            nest_user.get_nest_id(),
            int(params['grouping_spreadsheet_id']),
            int(params['grouping_feature_idx']),
            int(params['duration_spreadsheet_id']),
            int(params['duration_feature_idx']),
            int(params['event_spreadsheet_id']),
            int(params['event_feature_idx']),
            params['event_val'])
    else:
        raise ValueError('Unknown calculation ' + calculation_name)
    return return_val

def handle_error(job, ex_type, ex_value, traceback):
    """
    Handles any exception in a running job by updating the job status in the db.

    Arguments:
        job (rq.Job): the current job
        ex_type (class): the exception type
        ex_value (Exception): the exception object
        traceback (traceback): the exception traceback
    """
    # RQ already logs the error for us
    if job.func_name == 'nest_py.knoweng.jobs.worker_app.run_job':
        nest_user = job.args[0]
        user_id = nest_user.get_nest_id()
        job_id = job.args[1]
        if job_id:
            update_job_record(user_id, job_id, \
                {
                    'status': 'failed',
                    'error': 'Unknown error: ' + str(ex_value)
                })

def start_worker_subprocess(queues):
    """Starts an RQ worker subprocess.

    Args:
        queues (list): A list of the Queues for the subprocess to consume.

    Returns:
        None.

    """
    # make sure each subprocess has its own db connections
    init_crud_clients()
    Worker(queues, exception_handlers=[handle_error]).work()

def main():
    """Starts the RQ worker."""

    init_token_maker(CONFIG['JWT_SECRET'], CONFIG['JWT_ISSUER'], \
        CONFIG['JWT_AUDIENCES'])
    init_crud_clients()

    # If SEED_DATABASE is set to anything but the empty string, seed KN data into Postgres
    # TODO: this would be a good place to seed Redis too, if possible
    # FIXME: parameterize data directory?
    if os.getenv('SEED_DATABASE', '') != '':
        LOGGER.info('Seeding Postgres with KN data...')
        data_dir = '/code_live/data/projects/knoweng'
        exit_code = knoweng_seed_job.run(None, None, data_dir, None, None)

        if exit_code != 0:
            LOGGER.warning('WARNING: non-zero exit code from seed command:' + str(exit_code))
        LOGGER.info('Seeding complete!')
    else:
        LOGGER.info('Skipping Postgres seed, assuming data already exists...')

    with Connection(Redis(\
            host=CONFIG['REDIS_HOST'], db=CONFIG['JOB_QUEUE_REDIS_DB'])):
        # provide queue names to monitor
        queues = [Queue(CONFIG['JOB_QUEUE_DEFAULT_NAME'])]

        workers = []
        for i in range(CONFIG['JOB_QUEUE_WORKERS']):
            process = multiprocessing.Process(\
                target=start_worker_subprocess, args=(queues,))
            workers.append(process)
            process.start()

if __name__ == '__main__':
    main()
