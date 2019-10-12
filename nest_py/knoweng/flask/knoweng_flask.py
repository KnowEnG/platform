import os

from nest_py.core.flask.nest_endpoints.nest_endpoint_set import NestEndpointSet

from nest_py.core.flask.nest_endpoints.logging_endpoint import LoggingEndpoint
from nest_py.core.flask.nest_endpoints.sessions_endpoint import SessionsEndpoint
from nest_py.core.flask.nest_endpoints.status_endpoint import StatusEndpoint
import nest_py.core.flask.nest_endpoints.tablelike_endpoints as tablelike_endpoints

import nest_py.knoweng.db.knoweng_db as knoweng_db
import nest_py.knoweng.data_types.knoweng_schemas as knoweng_schemas
import nest_py.knoweng.data_types.analysis_networks as analysis_networks
import nest_py.knoweng.data_types.collections as collections
import nest_py.knoweng.data_types.feature_prioritizations as feature_prioritizations
import nest_py.knoweng.data_types.gene_set_characterizations as gene_set_characterizations
import nest_py.knoweng.data_types.public_gene_sets as public_gene_sets
import nest_py.knoweng.data_types.sample_clusterings as sample_clusterings
import nest_py.knoweng.data_types.signature_analyses as signature_analyses
import nest_py.knoweng.data_types.ssviz_jobs_spreadsheets as ssviz_jobs_spreadsheets
import nest_py.knoweng.data_types.ssviz_feature_correlations as ssviz_feature_correlations
import nest_py.knoweng.data_types.ssviz_feature_data as ssviz_feature_data
import nest_py.knoweng.data_types.ssviz_feature_variances as ssviz_feature_variances
import nest_py.knoweng.data_types.ssviz_spreadsheets as ssviz_spreadsheets
import nest_py.knoweng.data_types.jobs as jobs
import nest_py.knoweng.data_types.files as files
import nest_py.knoweng.data_types.projects as projects
import nest_py.knoweng.data_types.species as species

from nest_py.knoweng.flask.nest_endpoints.job_downloads_endpoint import JobDownloadsEndpoint
from nest_py.knoweng.flask.nest_endpoints.file_downloads_endpoint import FileDownloadsEndpoint
import nest_py.knoweng.flask.nest_endpoints.jobs_endpoints as jobs_endpoints
import nest_py.knoweng.flask.nest_endpoints.files_endpoints as files_endpoints
import nest_py.knoweng.flask.nest_endpoints.projects_endpoints as projects_endpoints
import nest_py.knoweng.flask.nest_endpoints.ssviz_endpoints as ssviz_endpoints

import nest_py.core.db.db_ops_utils as db_ops_utils
from nest_py.nest_envs import ProjectEnv, RunLevel
#from nest_py.ops.seed_ops import _run_seed_cmd

def get_nest_endpoints(db_engine, sqla_metadata, authenticator):
    all_eps = NestEndpointSet()

    schema_registry = knoweng_schemas.get_schemas()
    sqla_registry = knoweng_db.get_sqla_makers()

    ##STANDARD CRUD ENDPOINTS
    standard_eps = _make_standard_crud_endpoints(
        schema_registry, sqla_registry, authenticator,
        db_engine, sqla_metadata)
    all_eps.add_endpoint_set(standard_eps)

    ##SYSTEM STATUS
    status_endpoint = StatusEndpoint(authenticator)
    all_eps.add_endpoint(status_endpoint)

    ##CLIENT LOGGING
    logging_endpoint = LoggingEndpoint(authenticator)
    all_eps.add_endpoint(logging_endpoint)

    ####FILES
    files_db_client = sqla_registry[files.COLLECTION_NAME].get_db_client(
        db_engine, sqla_metadata)
    files_endpoints_set = files_endpoints.get_endpoint_set(
        files_db_client, authenticator)
    all_eps.add_endpoint_set(files_endpoints_set)


    ####FILE DOWNLOADS
    files_download_endpoint = FileDownloadsEndpoint(files_db_client, authenticator)
    all_eps.add_endpoint(files_download_endpoint)

    ####PROJECTS
    projects_db_client = sqla_registry[projects.COLLECTION_NAME].get_db_client(
        db_engine, sqla_metadata)
    projects_endpoints_set = projects_endpoints.get_endpoint_set(
        projects_db_client, authenticator)
    all_eps.add_endpoint_set(projects_endpoints_set)

    ###JOBS
    jobs_db_client = sqla_registry[jobs.COLLECTION_NAME].get_db_client(
        db_engine, sqla_metadata)
    jobs_endpoints_set = jobs_endpoints.get_endpoint_set(
        jobs_db_client, authenticator)
    all_eps.add_endpoint_set(jobs_endpoints_set)

    ###JOB DOWNLOADS
    jobs_download_endpoint = JobDownloadsEndpoint(jobs_db_client, authenticator)
    all_eps.add_endpoint(jobs_download_endpoint)

    ##LOGIN
    sessions_endpoint = SessionsEndpoint(authenticator)
    all_eps.add_endpoint(sessions_endpoint)

    ##SSVIZ related endpoint with POST, PATCH operations disabled
    ssviz_eps = _make_ssv_crud_endpoints(schema_registry, sqla_registry, authenticator, db_engine, sqla_metadata)
    all_eps.add_endpoint_set(ssviz_eps)

    #
    project_env_str = os.getenv('PROJECT_ENV', 'knoweng')
    runlevel_str = os.getenv('NEST_RUNLEVEL', 'development')

    project_env = ProjectEnv(project_env_str)
    runlevel = RunLevel(runlevel_str)

    #FIXME: lock DB to prevent duplication errors?
    if os.getpid() % 2 == 0:
        db_ops_utils.ensure_tables_in_db()
        db_ops_utils.seed_users(project_env, runlevel)

    # FIXME: seed the database with /networks files
    #exit_code = _run_seed_cmd({ 'project': project_env_str })
    #if exit_code != 0:
    #    print('WARNING: non-zero exit code from seed command:' + exit_code)

    return all_eps

def _make_standard_crud_endpoints(schema_registry, sqla_registry, authenticator, db_engine, sqla_metadata):
    """
    these are the datatypes that have standard schemas, and just need
    standard CRUD endpoints (no specialized behavior)
    """
    standard_eps = NestEndpointSet()

    standard_collections = [
        analysis_networks.COLLECTION_NAME,
        collections.COLLECTION_NAME,
        feature_prioritizations.COLLECTION_NAME,
        gene_set_characterizations.COLLECTION_NAME,
        public_gene_sets.COLLECTION_NAME,
        sample_clusterings.COLLECTION_NAME,
        signature_analyses.COLLECTION_NAME,
        species.COLLECTION_NAME
        ]

    for ep_name in standard_collections:
        sqla_maker = sqla_registry[ep_name]
        schema = schema_registry[ep_name]
        db_client = sqla_maker.get_db_client(db_engine, sqla_metadata)
        eps = tablelike_endpoints.generate_endpoints(
            schema, db_client, authenticator)
        standard_eps.add_endpoint_set(eps)
    return standard_eps

def _make_ssv_crud_endpoints(schema_registry, sqla_registry, authenticator, db_engine, sqla_metadata):
    """
    these are the datatypes that have ssviz schemas, will keep standard GET and DELETE, but disable POST and PATCH
    """
    ssviz_eps = NestEndpointSet()

    ssv_collections = [
        ssviz_jobs_spreadsheets.COLLECTION_NAME,
        ssviz_feature_correlations.COLLECTION_NAME,
        ssviz_feature_data.COLLECTION_NAME,
        ssviz_feature_variances.COLLECTION_NAME,
        ssviz_spreadsheets.COLLECTION_NAME
        ]

    for ep_name in ssv_collections:
        sqla_maker = sqla_registry[ep_name]
        schema = schema_registry[ep_name]
        db_client = sqla_maker.get_db_client(db_engine, sqla_metadata)
        eps = ssviz_endpoints.generate_endpoints(
            schema, db_client, authenticator)
        ssviz_eps.add_endpoint_set(eps)

    ssv_survival_analyses_endpoint = \
        ssviz_endpoints.SsvizSurvivalAnalysesEndpoint(authenticator)
    ssviz_eps.add_endpoint(ssv_survival_analyses_endpoint)

    return ssviz_eps
