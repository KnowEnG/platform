
from nest_py.core.flask.nest_endpoints.nest_endpoint_set import NestEndpointSet

from nest_py.core.flask.nest_endpoints.logging_endpoint import LoggingEndpoint
from nest_py.core.flask.nest_endpoints.sessions_endpoint import SessionsEndpoint
import nest_py.core.flask.nest_endpoints.tablelike_endpoints as tablelike_endpoints

import nest_py.knoweng.db.knoweng_db as knoweng_db
import nest_py.knoweng.data_types.knoweng_schemas as knoweng_schemas
import nest_py.knoweng.data_types.analysis_networks as analysis_networks
import nest_py.knoweng.data_types.collections as collections
import nest_py.knoweng.data_types.gene_prioritizations as gene_prioritizations
import nest_py.knoweng.data_types.gene_set_characterizations as gene_set_characterizations
import nest_py.knoweng.data_types.public_gene_sets as public_gene_sets
import nest_py.knoweng.data_types.sample_clusterings as sample_clusterings
import nest_py.knoweng.data_types.jobs as jobs 
import nest_py.knoweng.data_types.files as files
import nest_py.knoweng.data_types.projects as projects 
import nest_py.knoweng.data_types.species as species

from nest_py.knoweng.flask.nest_endpoints.job_downloads_endpoint import JobDownloadsEndpoint
from nest_py.knoweng.flask.nest_endpoints.file_downloads_endpoint import FileDownloadsEndpoint
import nest_py.knoweng.flask.nest_endpoints.jobs_endpoints as jobs_endpoints
import nest_py.knoweng.flask.nest_endpoints.files_endpoints as files_endpoints
import nest_py.knoweng.flask.nest_endpoints.projects_endpoints as projects_endpoints

def get_nest_endpoints(db_engine, sqla_metadata, authenticator):
    all_eps = NestEndpointSet()

    schema_registry = knoweng_schemas.get_schemas()
    sqla_registry = knoweng_db.get_sqla_makers()

    ##STANDARD CRUD ENDPOINTS
    standard_eps = _make_standard_crud_endpoints(
        schema_registry, sqla_registry, authenticator, 
        db_engine, sqla_metadata)
    all_eps.add_endpoint_set(standard_eps)

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
    projects_db_client =  sqla_registry[projects.COLLECTION_NAME].get_db_client(
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
        gene_prioritizations.COLLECTION_NAME,
        gene_set_characterizations.COLLECTION_NAME,
        public_gene_sets.COLLECTION_NAME,
        sample_clusterings.COLLECTION_NAME,
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


