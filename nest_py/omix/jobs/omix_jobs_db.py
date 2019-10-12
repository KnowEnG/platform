"""
Utilities for setting up and interacting with the database from 
omix jobs (using a job_context object and the omix schemas/tables)
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

def init_db_resources(jcx):
    """

    """
    jcx.checkpoint('omix_jobs_db.init_db_resources begin')
    proj = ProjectEnv.mmbdb_instance()
    runlevel = RunLevel.development_instance()

    sqla_md = nest_db.get_global_sqlalchemy_metadata()
    sqla_engine = nest_db.get_global_sqlalchemy_engine()
    sqla_makers = get_sqla_makers()

    #make sure the database tables exist in the database, build
    #them if not
    jcx.log('Ensuring omix tables in database')
    for sqla_maker in sqla_makers.values():
        sqla_maker.get_sqla_table(sqla_md)
    db_ops_utils.ensure_tables_in_db()

    #add in the users from hello_world, so there is a user that
    #will own the data we generate in wix jobs. This will do nothing
    #if they are already in the database
    jcx.log('Ensuring omixusers in nest_users table')
    db_ops_utils.seed_users(proj, runlevel)

    #create db clients for all our tables and put them in the jcx
    #note that all of the clients have a user set so that someone
    #'owns' the data in the database that is generated through the client
    jcx.log('Building database clients for the jcx runtime()')
    client_registry = dict()
    for table_name in sqla_makers:
        db_client = sqla_makers[table_name].get_db_client(sqla_engine, sqla_md)
        jobs_auth.set_db_user(db_client, 'fakeuser')
        client_registry[table_name] = db_client


    #add the clients to the job context 'runtime' object instances, where the 
    #job's methods can access them
    if 'db_clients' in jcx.runtime():
        jcx.runtime()['db_clients'] += client_registry
    else: 
        jcx.runtime()['db_clients'] = client_registry

    jcx.checkpoint('omix_jobs_db.init_db_resources complete')
    return

def write_job_start(jcx, job_name):
    """
    creates a new database entry for a 'wix_run' using info from the current
    run. Sets the 'status' to 'running'
    """
    config = jcx.get_config_jdata()
    #note this is the name based on local run_XXX names. it will be
    #different then the 'id' column in the database
    local_run_name = str(jcx.get_run_id())
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
    jcx.set_runtime_object('wix_run_tle', tle)
    jcx.log("wix job started: " + str(tle.get_nest_id()))
    return

def write_job_end(jcx):
    """
    changes the status of the current job to "finished"
    """
    end_time = NestDate.now().to_jdata()
    status = 'finished'
    run_tle = jcx.runtime()['wix_run_tle']
    run_tle.set_value('status', status)
    run_tle.set_value('end_time', end_time)

    run_collection = wix_run.COLLECTION_NAME
    db_client = jcx.runtime()['db_clients'][run_collection]
    run_tle = db_client.update_entry(run_tle)
    assert(not run_tle is None)

    jcx.log('wix job finished: ' + str(run_tle.get_nest_id()))
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

def get_sqla_makers():
    """
    returns a dict of (name(str) -> SqlaMaker)
    """
    registry = dict()
    for schema in omix_schemas.get_schemas().values():
        sqla_maker = TablelikeSqlaMaker(schema)
        tbl_name = sqla_maker.get_table_name()
        registry[tbl_name] = sqla_maker
   
    #also add the standard nest_users table, which handles data ownership
    users_nm = nest_users.COLLECTION_NAME
    users_sqlam = core_db.get_nest_users_sqla_maker()
    registry[users_nm] = users_sqlam

    #wix job runs table
    wix_nm = wix_run.COLLECTION_NAME
    wix_schema = wix_run.generate_schema()
    wix_sqlam = TablelikeSqlaMaker(wix_schema)
    registry[wix_nm] = wix_sqlam

    return registry


