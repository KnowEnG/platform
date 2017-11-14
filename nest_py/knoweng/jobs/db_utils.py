"""
This module defines methods to read and write job-related records in the DB.
"""
from datetime import timedelta
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
import nest_py.knoweng.data_types.gene_prioritizations as gene_prioritizations
import nest_py.knoweng.data_types.sample_clusterings as sample_clusterings
import nest_py.knoweng.data_types.collections as collections
import nest_py.knoweng.data_types.public_gene_sets as public_gene_sets
import nest_py.knoweng.data_types.analysis_networks as analysis_networks
import nest_py.knoweng.data_types.species as species
import nest_py.knoweng.db.knoweng_db as knoweng_db
import nest_py.knoweng.api_clients.knoweng_api_clients as knoweng_api_clients
from nest_py.nest_envs import ProjectEnv, RunLevel
import nest_py.core.nest_config as nest_config
TOKEN_MAKER = None


#Collections to access using API clients. Collections that 
#have specialized endpoint behavior with side effects 
#(like 'files' uploading) must be in this list
API_COLLECTIONS = [
    jobs.COLLECTION_NAME,
    files.COLLECTION_NAME,
#    gene_set_characterizations.COLLECTION_NAME,
#    gene_prioritizations.COLLECTION_NAME,
#    sample_clusterings.COLLECTION_NAME,
]

#Collections that only have default CRUD behavior can
#access the DB directly for improved efficiency and
#the clients are drop in replacements for the api clients
DB_COLLECTIONS = [
    gene_set_characterizations.COLLECTION_NAME,
    gene_prioritizations.COLLECTION_NAME,
    sample_clusterings.COLLECTION_NAME,
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
        server_address="flask",
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
        user_id (nest_id): The user_id of the Eve user who created the job.
        job_id (nest_id): The unique identifier Eve/Mongo assigns to the job.

        Returns:
            TablelikeEntry for a job entry
    """
    tle_crud_client = get_crud_client(jobs.COLLECTION_NAME, user_id)
    job_tle = tle_crud_client.read_entry(job_id)
    return job_tle

def update_job_record(user_id, job_id, merge_dict):
    """Updates a job record in the databse.

        Args:
        user_id (NestId): The user_id of the Eve user who created the job.
        job_id (NestId): The unique identifier Eve/Mongo assigns to the job.
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
        raise IOError("couldn't update " + job_id + " with " + str(merge_dict))

def get_file_record(user_id, file_id):
    """Gets a file record from the databse.

        Args:
        user_id (NestId): The user_id of the Eve user who created the file.
        file_id (NestId): The unique identifier Eve/Mongo assigns to the file.

        Returns:
            FileDTO

    """
    tle_crud_client = get_crud_client(files.COLLECTION_NAME, user_id)
    tle = tle_crud_client.read_entry(file_id)
    fdto = FileDTO.from_tablelike_entry(tle)
    return fdto

# TODO refactor; make sure TOKEN_MAKER is visible elsewhere
def create_gsc_record(user_id, job_id, user_gene_sets, set_level_scores,\
    minimum_score):
    """Stores results in the database.

        Args:
        user_id (NestId): The user_id of the Eve user who created the job.
        job_id (NestId): The unique identifier Eve/Mongo assigns to the job.
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
    #created_id = crud_client.create_entry(gsc_tle, timeout_secs=50000)
    created_id = crud_client.create_entry(gsc_tle)
    if created_id is None:
        # TODO improve error handling
        raise IOError("couldn't save GSC results for " + job_id)
    return

def create_gp_record(user_id, job_id, scores, minimum_score,\
    gene_id_to_name_dict):
    """Stores results in the database.

        Args:
        user_id (Nestid): The user_id of the Eve user who created the job.
        job_id (NestId): The unique identifier Eve/Mongo assigns to the job.
        scores (dict): The list generated in on_done().
        minimum_score (float): The smallest score that should be colored in the
            heatmap.
        gene_id_to_name_dict (dict): A dict in which the keys are gene ids and
            the values are gene names.

        Returns:
            None: None.

    """
    gp_name = gene_prioritizations.COLLECTION_NAME
    crud_client = get_crud_client(gp_name, user_id)
    gp_data = {
        'job_id': job_id,
        'scores': scores,
        'minimum_score': minimum_score,
        'gene_ids_to_names': gene_id_to_name_dict
        }
    gp_tle = TablelikeEntry(SCHEMA_REGISTRY[gp_name])
    gp_tle.set_data_dict(gp_data)

    # write the results to the db
    #created_id = crud_client.create_entry(gp_tle, timeout_secs=50000)
    created_id = crud_client.create_entry(gp_tle)
    if created_id is None:
        # TODO improve error handling
        raise IOError("couldn't save GP results for " + job_id)
    return


def create_sc_record(user_id, job_id, top_genes, samples, genes_heatmap,\
    samples_heatmap, phenotypes):
    """Stores results in the database.

        Args:
        user_id (NestId): The user_id of the Eve user who created the job.
        job_id (NestId): The unique identifier Eve/Mongo assigns to the job.
        top_genes (dict): The dictionary generated by `get_top_genes`.
        samples (list): The list generated by `get_ordered_samples`.
        genes_heatmap (list): The 2D list returned by `get_genes_heatmap`.
        samples_heatmap (list): The 2D list returned by `get_samples_heatmap`.
        phenotypes (list): The list returned by TODO FIXME.

        Returns:
            None: None.

    """
    sc_name = sample_clusterings.COLLECTION_NAME
    crud_client = get_crud_client(sc_name, user_id)

    sc_data = {
        'job_id': job_id,
        'top_genes': top_genes,
        'samples': samples,
        'genes_heatmap': genes_heatmap,
        'samples_heatmap': samples_heatmap,
        'phenotypes': phenotypes
        }
    sc_tle = TablelikeEntry(SCHEMA_REGISTRY[sc_name])
    sc_tle.set_data_dict(sc_data)

    # write the results to the db
    #created_id = crud_client.create_entry(sc_tle, timeout_secs=50000)
    created_id = crud_client.create_entry(sc_tle)
    if created_id is None:
        # TODO improve error handling
        raise IOError("couldn't save SC results for " + job_id)
    return
