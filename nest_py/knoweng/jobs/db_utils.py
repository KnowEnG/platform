"""
This module defines methods to read and write job-related records in the DB.
"""
from datetime import timedelta
import logging
from numbers import Number
from shutil import copyfile

import numpy as np

from nest_py.core.flask.accounts.token import TokenAgent
from nest_py.core.api_clients.http_client import NestHttpClient
from nest_py.core.data_types.nest_id import NestId
from nest_py.core.data_types.nest_user import NestUser
from nest_py.core.data_types.tablelike_entry import TablelikeEntry
import nest_py.core.db.nest_db as nest_db
import nest_py.knoweng.data_types.knoweng_schemas as knoweng_schemas
import nest_py.knoweng.data_types.files as files
from nest_py.knoweng.data_types.files import FileDTO
import nest_py.knoweng.data_types.jobs as jobs
import nest_py.knoweng.data_types.gene_set_characterizations as gene_set_characterizations
import nest_py.knoweng.data_types.feature_prioritizations as feature_prioritizations
import nest_py.knoweng.data_types.sample_clusterings as sample_clusterings
import nest_py.knoweng.data_types.signature_analyses as signature_analyses
import nest_py.knoweng.data_types.ssviz_jobs_spreadsheets as ssviz_jobs_spreadsheets
import nest_py.knoweng.data_types.ssviz_feature_correlations as ssviz_feature_correlations
import nest_py.knoweng.data_types.ssviz_feature_data as ssviz_feature_data
import nest_py.knoweng.data_types.ssviz_feature_variances as ssviz_feature_variances
import nest_py.knoweng.data_types.ssviz_spreadsheets as ssviz_spreadsheets
import nest_py.knoweng.data_types.collections as collections
import nest_py.knoweng.data_types.public_gene_sets as public_gene_sets
import nest_py.knoweng.data_types.analysis_networks as analysis_networks
import nest_py.knoweng.data_types.species as species
import nest_py.knoweng.db.knoweng_db as knoweng_db
import nest_py.knoweng.api_clients.knoweng_api_clients as knoweng_api_clients
from nest_py.nest_envs import ProjectEnv, RunLevel
import nest_py.core.nest_config as nest_config

LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.INFO)

TOKEN_MAKER = None

#Collections to access using API clients. Collections that
#have specialized endpoint behavior with side effects
#needed for jobs must appear here. Note that though the files
#endpoint has specialized behavior, we don't need it here.
API_COLLECTIONS = [
    jobs.COLLECTION_NAME
]

#Collections that only have default CRUD behavior can
#access the DB directly for improved efficiency and
#the clients are drop in replacements for the api clients
DB_COLLECTIONS = [
    files.COLLECTION_NAME,
    gene_set_characterizations.COLLECTION_NAME,
    feature_prioritizations.COLLECTION_NAME,
    sample_clusterings.COLLECTION_NAME,
    signature_analyses.COLLECTION_NAME,
    ssviz_jobs_spreadsheets.COLLECTION_NAME,
    ssviz_feature_correlations.COLLECTION_NAME,
    ssviz_feature_data.COLLECTION_NAME,
    ssviz_feature_variances.COLLECTION_NAME,
    ssviz_spreadsheets.COLLECTION_NAME,
    public_gene_sets.COLLECTION_NAME,
    analysis_networks.COLLECTION_NAME,
    collections.COLLECTION_NAME,
    species.COLLECTION_NAME,
    ]


#dict from schema name -> schema
SCHEMA_REGISTRY = None

#dict from schema name -> crud client (db or api)
CLIENT_REGISTRY = None


def init_token_maker(secret, issuer, audiences):
    """Initializes TOKEN_MAKER.

    Arguments:
        secret (str): Symmetric secret for token signing.
        issuer (str): Issuer to claim in the token.
        audiences(List[str]): Audiences to claim in the token.

    Returns:
        None
    """
    global TOKEN_MAKER
    TOKEN_MAKER = TokenAgent(secret, issuer, audiences)

def init_crud_clients():
    config = nest_config.generate_config(
        ProjectEnv.knoweng_instance(),
        RunLevel.development_instance())
    init_token_maker(
        config['JWT_SECRET'],
        config['JWT_ISSUER'],
        config['JWT_AUDIENCES'])

    global SCHEMA_REGISTRY
    SCHEMA_REGISTRY = knoweng_schemas.get_schemas()
    global CLIENT_REGISTRY
    CLIENT_REGISTRY = dict()

    #make db clients

    #TODO: knoweng should declare the db it's using, but for now
    #the default postgres container on localhost is all there is,
    #which is what the global db engine defaults to.
    engine = nest_db.get_global_sqlalchemy_engine()
    # make sure each multiprocessing Process has its own connection
    # http://docs.sqlalchemy.org/en/rel_0_9/core/connections.html#engine-disposal
    # TODO more general solution
    engine.dispose()
    sqla_md = nest_db.get_global_sqlalchemy_metadata()
    db_client_makers = knoweng_db.get_sqla_makers()
    for name in DB_COLLECTIONS:
        cm = db_client_makers[name]
        client = cm.get_db_client(engine, sqla_md)
        CLIENT_REGISTRY[name] = client

    #make api clients

    http_client = get_http_client()
    api_client_makers = knoweng_api_clients.get_api_client_makers()
    for name in API_COLLECTIONS:
        cm = api_client_makers[name]
        crud_client = cm.get_crud_client(http_client)
        CLIENT_REGISTRY[name] = crud_client
    return

def login_client(crud_client, user_id):

    if crud_client.get_collection_name() in DB_COLLECTIONS:
        #TODO: this should look up the actual NestUser, but for now the
        #DB client only uses the valid ID.
        nest_user = NestUser(user_id, None, None, None)
        crud_client.set_requesting_user(nest_user)
    elif crud_client.get_collection_name() in API_COLLECTIONS:
        token = TOKEN_MAKER.create_for_system_operation_as_user(\
            user_id, timedelta(minutes=10)) # 10 minutes in case of clock skew
        crud_client.get_http_client().set_auth_token(token)
    else:
        raise Exception('client is neither in API or DB clients')
    return

def get_http_client(auth_token=None):
    """Returns an http_client for nest_flask.

    Arguments:
        auth_token (Optional[str]): authentication token to use with all
            requests.

    Returns:
        NestHttpClient
    """
    # note: at least until we switch from docker links to docker networks,
    # when connecting to http://flask, we need to use the container port,
    # not the host port
    return NestHttpClient(
        server_address="localhost",
        server_port=80,
        auth_token=auth_token)

def get_crud_client(collection_name, user_id=None):
    client = CLIENT_REGISTRY[collection_name]
    if user_id is None:
        user_id = NestId(2) #a hack for the knoweng seed job
    login_client(client, user_id)
    return client

def get_job_record(user_id, job_id):
    """Gets a job record from the databse.

    Args:
        user_id (NestId): The user_id of the user who created the job.
        job_id (NestId): The job id associated with the job.

    Returns:
        TablelikeEntry for a job entry
    """
    tle_crud_client = get_crud_client(jobs.COLLECTION_NAME, user_id)
    job_tle = tle_crud_client.read_entry(job_id)
    return job_tle

def update_job_record(user_id, job_id, merge_dict):
    """Updates a job record in the databse.

    Args:
        user_id (NestId): The user_id of the user who created the job.
        job_id (NestId): The job id associated with the job.
        merge_dict (dictionary): A dictionary of key-value pairs to merge into
            the job record in the database.

    Returns:
        None: None.

    """
    # read the current job document--we can't overwrite it unless we know the
    # current contents
    job_tle = get_job_record(user_id, job_id)
    job_tle.get_data_dict().update(merge_dict)
    tle_crud_client = get_crud_client(jobs.COLLECTION_NAME, user_id)
    # write the job back to the db
    updated_id = tle_crud_client.update_entry(job_id, job_tle, timeout_secs=500)
    if updated_id is None:
        # TODO improve error handling
        raise IOError("couldn't update " + job_id.to_slug() + " with " + \
            str(merge_dict))

def get_file_record(user_id, file_id):
    """Gets a file record from the databse.

    Args:
        user_id (NestId): The user_id of the user who created the job.
        job_id (NestId): The job id associated with the job.

    Returns:
        FileDTO

    """
    tle_crud_client = get_crud_client(files.COLLECTION_NAME, user_id)
    tle = tle_crud_client.read_entry(file_id)
    fdto = FileDTO.from_tablelike_entry(tle)
    return fdto

def create_file_record(user_id, job_id, project_id, userfiles_dir, \
    source_path, filename=None):
    """Writes file info to the database, typically so that a file generated by
    analytics will appear in the user's collection of files.

    Args:
        user_id (NestId): The user_id of the user who created the job.
        job_id (NestId): The unique identifier assigned to the job.
        project_id (NestId): The project id associated with the job.
        userfiles_dir (str): The path to the userfiles directory.
        source_path (str): The path to the file on local disk.
        filename (str): The filename to use in the DB record, or None to use
            the same name as on disk.

    Returns:
        FileDTO: A FileDTO representation of the file.

    """
    collection_name = files.COLLECTION_NAME
    crud_client = get_crud_client(collection_name, user_id)

    file_tle = files.generate_file_tle_for_local_file(\
        source_path, project_id, job_id, filename)
    created_tle = crud_client.create_entry(file_tle)
    if created_tle is None:
        # TODO improve error handling
        raise IOError("couldn't create file record for " + source_path + \
            " on job " + job_id.to_slug())
    file_dto = FileDTO.from_tablelike_entry(created_tle)
    target_path = file_dto.get_file_path(userfiles_dir)
    files.prepare_files_dirpath(userfiles_dir, project_id)
    copyfile(source_path, target_path)
    return file_dto

# TODO refactor; make sure TOKEN_MAKER is visible elsewhere
def create_gsc_record(user_id, job_id, user_gene_sets, set_level_scores,\
    minimum_score):
    """Stores results in the database.

    Args:
        user_id (NestId): The user_id of the user who created the job.
        job_id (NestId): The job id associated with the job.
        user_gene_sets (list): The list returned by get_user_gene_sets().
        set_level_scores (dict): The dict returned by get_set_level_scores().
        minimum_score (float): The smallest score that should be colored in the
            heatmap.

    Returns:
        None: None.

    """
    gsc_name = gene_set_characterizations.COLLECTION_NAME
    crud_client = get_crud_client(gsc_name, user_id)
    gsc_data = {
        'job_id': job_id,
        'user_gene_sets': user_gene_sets,
        'set_level_scores': set_level_scores,
        'minimum_score': minimum_score
    }
    gsc_tle = TablelikeEntry(SCHEMA_REGISTRY[gsc_name])
    gsc_tle.set_data_dict(gsc_data)

    # write the results to the db
    created_tle = crud_client.create_entry(gsc_tle)
    if created_tle is None:
        # TODO improve error handling
        raise IOError("couldn't save GSC results for " + job_id.to_slug())

def create_fp_record(user_id, job_id, scores, minimum_score,\
    feature_id_to_name_dict):
    """Stores results in the database.

    Args:
        user_id (NestId): The user_id of the user who created the job.
        job_id (NestId): The job id associated with the job.
        scores (dict): The dict generated in on_done().
        minimum_score (float): The smallest score that should be colored in the
            heatmap.
        feature_id_to_name_dict (dict): A dict in which the keys are feature ids
            and the values are feature names.

    Returns:
        None: None.

    """
    fp_name = feature_prioritizations.COLLECTION_NAME
    crud_client = get_crud_client(fp_name, user_id)
    fp_data = {
        'job_id': job_id,
        'scores': scores,
        'minimum_score': minimum_score,
        'feature_ids_to_names': feature_id_to_name_dict
        }
    fp_tle = TablelikeEntry(SCHEMA_REGISTRY[fp_name])
    fp_tle.set_data_dict(fp_data)

    # write the results to the db
    created_tle = crud_client.create_entry(fp_tle)
    if created_tle is None:
        # TODO improve error handling
        raise IOError("couldn't save FP results for " + job_id.to_slug())

def create_sc_record(user_id, job_id, consensus_matrix_df,\
    consensus_matrix_file_id, initial_column_grouping_file_id,\
    initial_column_grouping_feature_index, initial_column_sorting_file_id,\
    initial_column_sorting_feature_index, global_silhouette_score,\
    cluster_silhouette_scores):
    """Stores results in the database.

    Args:
        user_id (NestId): The user_id of the user who created the job.
        job_id (NestId): The job id associated with the job.
        consensus_matrix_df (pandas.DataFrame): A DataFrame containing the
            consensus matrix, or None if bootstrapping wasn't used.
        consensus_matrix_file_id (NestId): The file id associated with the
            consensus matrix file, or None if bootstrapping wasn't used.
        initial_column_grouping_file_id (NestId): The file id associated with
            the initial column grouping; i.e., file id of the file containing
            the cluster labels.
        initial_column_grouping_feature_index (int): The index of the feature in
            `initial_column_grouping_file_id` that serves as the initial column
            grouping; i.e., the feature index of the cluster labels within their
            file.
        initial_column_sorting_file_id (NestId): The file id associated with
            the initial column sorting.
        initial_column_sorting_feature_index (int): The index of the feature in
            `initial_column_sorting_file_id` that serves as the initial column
            sorting.
        global_silhouette_score (float): The job-level silhouette score.
        cluster_silhouette_scores (list): A list of floats, each of which is a
            cluster-level silhouette score, in cluster-label order.

    Returns:
        None: None.

    """
    sc_name = sample_clusterings.COLLECTION_NAME
    crud_client = get_crud_client(sc_name, user_id)

    consensus_matrix_labels = consensus_matrix_df.index.tolist() if \
        consensus_matrix_df is not None else []
    consensus_matrix_values = consensus_matrix_df.values.tolist() if \
        consensus_matrix_df is not None else []

    sc_data = {
        'job_id': job_id,
        'consensus_matrix_labels': consensus_matrix_labels,
        'consensus_matrix_values': consensus_matrix_values,
        'consensus_matrix_file_id': consensus_matrix_file_id,
        'init_col_grp_file_id': initial_column_grouping_file_id,
        'init_col_grp_feature_idx': initial_column_grouping_feature_index,
        'init_col_srt_file_id': initial_column_sorting_file_id,
        'init_col_srt_feature_idx': initial_column_sorting_feature_index,
        'global_silhouette_score': global_silhouette_score,
        'cluster_silhouette_scores': cluster_silhouette_scores
        }
    sc_tle = TablelikeEntry(SCHEMA_REGISTRY[sc_name])
    sc_tle.set_data_dict(sc_data)

    # write the results to the db
    created_tle = crud_client.create_entry(sc_tle)
    if created_tle is None:
        # TODO improve error handling
        raise IOError("couldn't save SC results for " + job_id.to_slug())

def create_sa_record(user_id, job_id, scores):
    """Stores results in the database.

    Args:
        user_id (NestId): The user_id of the user who created the job.
        job_id (NestId): The job id associated with the job.
        scores (dict): The dict generated in on_done().

    Returns:
        None: None.

    """
    sa_name = signature_analyses.COLLECTION_NAME
    crud_client = get_crud_client(sa_name, user_id)
    sa_data = {
        'job_id': job_id,
        'scores': scores,
        }
    sa_tle = TablelikeEntry(SCHEMA_REGISTRY[sa_name])
    sa_tle.set_data_dict(sa_data)

    # write the results to the db
    created_tle = crud_client.create_entry(sa_tle)
    if created_tle is None:
        # TODO improve error handling
        raise IOError("couldn't save SA results for " + job_id.to_slug())


def get_ssviz_spreadsheets_by_file_ids(user_id, file_ids):
    """Gets records in ssviz_spreadsheets where file_id matches an item in the
    provided list `file_ids`.

        Args:
        user_id (NestId): The user_id of the user who created the job.
        file_ids (list): The list of file_ids that should constrain the search.

        Returns:
            list: A list of TablelikeEntry objects for the matches.

    """
    collection_name = ssviz_spreadsheets.COLLECTION_NAME
    crud_client = get_crud_client(collection_name, user_id)

    return crud_client.simple_filter_query(\
        {'file_id': [file_id.get_value() for file_id in file_ids]})

def get_ssviz_feature_data(user_id, spreadsheet_id, feature_idxs):
    """Gets records in ssviz_feature_data where the ssviz_spreadsheet_id matches
    the provided `spreadsheet_id` and the feature_idx matches an item in the
    provided list `feature_idxs`.

        Args:
        user_id (NestId): The user_id of the user who created the job.
        spreadsheet_id (int): The constraint for ssviz_spreadsheet_id.
        feature_idxs (list): The list of feature_idxs that should constrain the
            search.

        Returns:
            list: A list of TablelikeEntry objects for the matches.

    """
    collection_name = ssviz_feature_data.COLLECTION_NAME
    crud_client = get_crud_client(collection_name, user_id)

    return crud_client.simple_filter_query(\
        {'ssviz_spreadsheet_id': spreadsheet_id, 'feature_idx': feature_idxs})

def get_ssviz_spreadsheets_by_ids(user_id, spreadsheet_ids):
    """Gets records in ssviz_spreadsheets where id matches an item in the
    provided list `spreadsheet_ids`.

        Args:
        user_id (NestId): The user_id of the user who created the job.
        spreadsheet_ids (list): The list of spreadsheet ids as integers that
            should constrain the search.

        Returns:
            list: A list of TablelikeEntry objects for the matches.

    """
    collection_name = ssviz_spreadsheets.COLLECTION_NAME
    crud_client = get_crud_client(collection_name, user_id)

    return crud_client.simple_filter_query({'id': spreadsheet_ids})

def create_ssviz_spreadsheet_and_feature_data(user_id, file_id,\
        is_file_samples_as_rows, sample_names, feature_names, feature_types,\
        feature_nan_counts, sample_nan_counts, ss_df):
    """Creates a record in ssviz_spreadsheet and records in ssviz_feature_data
    for a spreadsheet used in SSV.

        Args:
        user_id (NestId): The user_id of the user who created the job.
        file_id (NestId): The file_id of the file record for the spreadsheet.
        is_file_samples_as_rows (bool): Whether the original file was oriented
            such that samples corresponded to rows.
        sample_names (list): A list of the sample identifiers, ordered as they
            appear in the source file.
        feature_names (list): A list of the feature identifiers, ordered as they
            appear in the source file.
        feature_types (list): A list of the feature types, ordered to match
            `feature_names`.
        feature_nan_counts (list): A list of numbers, with each number
            indicating the numer of nans in a feature.
        sample_nan_counts (list): A list of numbers, with each number indicating
            the number of nans in a sample.
        ss_df (pandas.DataFrame): The data frame containing the spreadsheet
            data, oriented such that features corespond to columns (note this is
            different from the on-screen orientation).

        Returns:
            NestId: The NestId for the ssviz_spreadsheets entry.

    """
    # prepare to write the spreadsheet to the DB
    collection_name = ssviz_spreadsheets.COLLECTION_NAME
    crud_client = get_crud_client(collection_name, user_id)

    spreadsheet_data = {
        'file_id': file_id,
        'is_file_samples_as_rows': is_file_samples_as_rows,
        'sample_names': sample_names,
        'feature_names': feature_names,
        'feature_types': feature_types,
        'feature_nan_counts': feature_nan_counts,
        'sample_nan_counts': sample_nan_counts
        }
    spreadsheet_tle = TablelikeEntry(SCHEMA_REGISTRY[collection_name])
    spreadsheet_tle.set_data_dict(spreadsheet_data)

    # write the spreadsheet to the DB
    created_tle = crud_client.create_entry(spreadsheet_tle)
    if created_tle is None:
        raise IOError("couldn't save SSV spreadsheet for file " + \
            file_id.to_slug())
    created_id = created_tle.get_nest_id()

    # prepare to write the rows to the DB
    collection_name = ssviz_feature_data.COLLECTION_NAME
    crud_client = get_crud_client(collection_name, user_id)

    tles = []
    for feature_idx, feature_name in enumerate(ss_df):
        feature = ss_df[feature_name]
        tle = TablelikeEntry(SCHEMA_REGISTRY[collection_name])
        tle.set_value('ssviz_spreadsheet_id', created_id)
        tle.set_value('feature_idx', feature_idx)
        # replace any numeric NaNs with Nones
        safe_values = [None if (isinstance(val, Number) and np.isnan(val)) \
            else val for val in feature.tolist()]
        tle.set_value('values', safe_values)
        tles.append(tle)

    # write the rows to the DB
    crud_client.bulk_create_entries_async(tles, batch_size=5000)
    return created_id

def create_ssviz_jobs_spreadsheets_entries(user_id, job_id,\
    ssviz_spreadsheet_ids):
    """Creates records in ssviz_jobs_spreadsheets for a SSV job.

        Args:
        user_id (Nestid): The user_id of the user who created the job.
        job_id (Nestid): The job_id of the job.
        ssviz_spreadsheet_ids (list(Nestid)): The ssviz_spreadsheet_id values
            for the job.

        Returns:
            None: None.

    """
    collection_name = ssviz_jobs_spreadsheets.COLLECTION_NAME
    crud_client = get_crud_client(collection_name, user_id)

    tles = []
    for ssviz_spreadsheet_id in ssviz_spreadsheet_ids:
        tle = TablelikeEntry(SCHEMA_REGISTRY[collection_name])
        tle.set_value('job_id', job_id)
        tle.set_value('ssviz_spreadsheet_id', ssviz_spreadsheet_id)
        tles.append(tle)

    crud_client.bulk_create_entries_async(tles)

def create_ssviz_feature_variances_entry(user_id, ssviz_spreadsheet_id, scores):
    """Creates a record in ssviz_feature_variances.

        Args:
        user_id (Nestid): The user_id of the user who created the job.
        ssviz_spreadsheet_id (Nestid): The ssviz_spreadsheet_id of the
            spreadsheet over which the variances were calculated.
        scores (list): The variances as a list of floats.

        Returns:
            None: None

    """
    collection_name = ssviz_feature_variances.COLLECTION_NAME
    crud_client = get_crud_client(collection_name, user_id)

    tle = TablelikeEntry(SCHEMA_REGISTRY[collection_name])
    tle.set_value('ssviz_spreadsheet_id', ssviz_spreadsheet_id)
    tle.set_value('scores', scores)

    created_tle = crud_client.create_entry(tle)
    if created_tle is None:
        raise IOError("couldn't save variances for spreadsheet id " + \
            ssviz_spreadsheet_id.to_slug())

def get_ssviz_spreadsheets_with_correlations(\
    user_id, ssviz_spreadsheet_ids):
    """Gets records in ssviz_feature_correlations where BOTH the
    ssviz_spreadsheet_id and the g_spreadsheet_id are found in
    the given list `ssviz_spreadsheet_ids`.

        Args:
        user_id (NestId): The user_id of the user who created the job.
        ssviz_spreadsheet_ids (list): The spreadsheets to search for.

        Returns:
            list: A list of TablelikeEntry objects for the matches.

    """
    collection_name = ssviz_feature_correlations.COLLECTION_NAME
    crud_client = get_crud_client(collection_name, user_id)

    ids_as_ints = [nid.get_value() for nid in ssviz_spreadsheet_ids]

    # could do a SELECT DISTINCT, but this should suffice for our volume
    return crud_client.simple_filter_query({
        'ssviz_spreadsheet_id': ids_as_ints,
        'g_spreadsheet_id': ids_as_ints})

def create_ssviz_feature_correlations_entry(user_id, ssviz_spreadsheet_id, \
    g_spreadsheet_id, g_feature_idx, scores):
    """Creates a record in ssviz_feature_correlations.

        Args:
        user_id (Nestid): The user_id of the user who created the job.
        ssviz_spreadsheet_id (Nestid): The ssviz_spreadsheet_id of the
            spreadsheet over which the correlations were calculated.
        g_spreadsheet_id (Nestid): The ssviz_spreadsheet_id of
            the spreadsheet that supplied the basis for grouping (see also
            `g_feature_idx`).
        g_feature_idx (int): The feature index of the feature within
            the spreadsheet specified by `g_spreadsheet_id`
            that supplied the basis for grouping.
        scores (list): The pvals as a list of floats.

        Returns:
            None: None

    """
    collection_name = ssviz_feature_correlations.COLLECTION_NAME
    crud_client = get_crud_client(collection_name, user_id)

    tle = TablelikeEntry(SCHEMA_REGISTRY[collection_name])
    tle.set_value('ssviz_spreadsheet_id', ssviz_spreadsheet_id)
    tle.set_value('g_spreadsheet_id', g_spreadsheet_id)
    tle.set_value('g_feature_idx', g_feature_idx)
    tle.set_value('scores', scores)

    created_tle = crud_client.create_entry(tle)
    if created_tle is None:
        raise IOError("couldn't save correlations for " + \
            ssviz_spreadsheet_id.to_slug() + " grouped by " + \
            g_spreadsheet_id.to_slug() + " feature " + \
            str(g_feature_idx))
