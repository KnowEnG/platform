"""
Standalone methods for working with the database entries that the
Wix environment itself is responsible for (in particular, the wix_run
table). The methods require a JobContext to already be available which
would normally be created by the Wix environment.
"""

import nest_py.omix.data_types.omix_schemas as omix_schemas
import nest_py.core.db.core_db as core_db
import nest_py.core.db.nest_db as nest_db
import nest_py.core.data_types.nest_user as nest_users
import nest_py.core.data_types.wix_run as wix_run
import nest_py.core.jobs.jobs_auth as jobs_auth
from nest_py.core.data_types.nest_date import NestDate
from nest_py.core.data_types.tablelike_entry import TablelikeEntry
from nest_py.core.db.tablelike_sqla import TablelikeSqlaMaker
from nest_py.nest_envs import ProjectEnv
from nest_py.nest_envs import RunLevel
import nest_py.core.db.db_ops_utils as db_ops_utils

def init_db_resources(jcx, nest_site=None, run_level=None):
    """
    Connects to the Postgres database and ensures the Wix
    environments tables exist and also that the default users
    are seeded (TODO: currently it's always the hello_world users).
    Also creates crud_clients for the Wix tables and puts them
    in the jcx.

    jcx(JobContext): JobContext of the wix run currently being
        initialized.
    nest_site(NestSite (or None for localhost)): The location
        of the Postgres instance to connect to for all
        tables (both the Wix environment tables and any others
        that the job itself uses).
    run_level(RunLevel (or None for 'development'): Passed
        to the nest_db config to use however it wants.

    """
    jcx.checkpoint('wix_db.init_db_resources begin')

    #set global host for db connections
    db_config = nest_db.generate_db_config(site=nest_site)
    nest_db.GLOBAL_SQLA_RESOURCES.set_config(db_config)

    wix_sqla_makers = get_wix_sqla_makers()

    #create db clients for all our tables and put them in the jcx
    #note that all of the clients have a user set so that someone
    #'owns' the data in the database that is generated through the client
    jcx.log('Building WIX core database clients for the jcx runtime()')

    init_db_clients(jcx, wix_sqla_makers)
    #add in the users from hello_world, so there is a user that
    #will own the data we generate in wix jobs. This will do nothing
    #if they are already in the database
    jcx.log('Ensuring users in nest_users table')
    proj = ProjectEnv.hello_world_instance()
    db_ops_utils.seed_users(proj, run_level)

    jcx.checkpoint('wix_db.init_db_resources complete')
    return

def init_db_clients(jcx, sqla_makers):
    """
    ensures the tables are in the database and creates
    database clients for all SqlaMaker's in the input
    dictionary. The clients are added to the jcx's 
    jcx.runtime()['db_clients']. 

    jcx: JobContext
    sqla_makers: dict of {table_name:str -> SqlaMaker}
    """
    #create db clients for all our tables and put them in the jcx
    #note that all of the clients have a user set so that someone
    #'owns' the data in the database that is generated through the client

    sqla_md = nest_db.get_global_sqlalchemy_metadata()
    sqla_engine = nest_db.get_global_sqlalchemy_engine()
    client_registry = dict()
    for table_name in sqla_makers:
        sqlm = sqla_makers[table_name]
        tbl = sqlm.get_sqla_table(sqla_md)
        if tbl.exists(sqla_engine):
            print(' exists : ' + str(tbl.name))
        else:
            tbl.create(sqla_engine)
            print(' CREATED: ' + str(tbl.name))
        db_client = sqlm.get_db_client(sqla_engine, sqla_md)
        username = 'fakeuser'
        jobs_auth.set_db_user(db_client, username)  #FIXME: needs to be job-specific user, currently works b/c all projects have user 'fakeuser'
        client_registry[table_name] = db_client

    #add the clients to the job context 'runtime' object instances, where the 
    #job's methods can access them
    if 'db_clients' in jcx.runtime():
        #if the registry exists, make the new one combine the old and new
        client_registry.update(jcx.runtime()['db_clients'])
    jcx.runtime()['db_clients'] = client_registry

    return

def write_job_start(jcx):
    """
    creates a new database entry for a 'wix_run' using info from the current
    run. Sets the 'status' to 'running'. Also adds the wix_run TablelikeEntry
    to the jcx as the 'wix_run_tle'.

    """
    job_name = jcx.get_job_key()
    config = jcx.get_config_jdata()
    local_run_name = None #local_run_name is essentially deprecated
    start_time = NestDate.now().to_jdata()
    end_time = None
    status = 'running'

    run_collection = wix_run.COLLECTION_NAME
    wix_run_schema = wix_run.generate_schema()
    tle = TablelikeEntry(wix_run_schema)
    tle.set_value('job_name', job_name)
    tle.set_value('local_results_name', local_run_name)
    tle.set_value('status', status)
    tle.set_value('start_time', start_time)
    tle.set_value('end_time', end_time)
    tle.set_value('config', config)

    db_client = jcx.runtime()['db_clients'][run_collection]
    tle = db_client.create_entry(tle)
    assert(not tle is None)

    #save the tle so we can update the status later
    jcx.set_wix_run_tle(tle)
    jcx.log("wix run db entry initialized as 'running' : " + str(jcx.get_wix_run_id()))
    return

def write_job_end(jcx):
    """
    Changes the status of the current job to "finished" in the database.
    Relies on the wix_run_tle having been set by wix_db.write_job_start()
    """
    end_time = NestDate.now().to_jdata()
    status = 'finished'
    run_tle = jcx.get_wix_run_tle()
    run_tle.set_value('status', status)
    run_tle.set_value('end_time', end_time)

    run_collection = wix_run.COLLECTION_NAME
    db_client = jcx.runtime()['db_clients'][run_collection]
    run_tle = db_client.update_entry(run_tle)
    assert(not run_tle is None)
    jcx.log("wix run db entry updated to 'finished'")

    return

def read_wix_run(jcx, wix_run_id):
    """
    wix_run_id (NestId)
    returns a tle for an existing wix_run in the DB
    """
    run_collection = wix_run.COLLECTION_NAME
    db_client = jcx.runtime()['db_clients'][run_collection]
    run_tle = db_client.read_entry(wix_run_id)
    return run_tle

def get_wix_sqla_makers():
    """
    Returns a dict of (name(str) -> SqlaMaker) related to the
    tables needed by the Wix environment itself.
    """
    registry = dict()
#   
    #add the standard nest_users table, which handles data ownership
    users_nm = nest_users.COLLECTION_NAME
    users_sqlam = core_db.get_nest_users_sqla_maker()
    registry[users_nm] = users_sqlam

    #wix job runs table
    wix_nm = wix_run.COLLECTION_NAME
    wix_schema = wix_run.generate_schema()
    wix_sqlam = TablelikeSqlaMaker(wix_schema)
    registry[wix_nm] = wix_sqlam

    return registry


