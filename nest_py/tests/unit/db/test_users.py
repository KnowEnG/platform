
import nest_py.core.db.nest_db as nest_db
import nest_py.core.db.core_db as core_db
import nest_py.core.db.db_ops_utils as db_ops_utils
import nest_py.core.data_types.nest_user as nest_users
import nest_py.knoweng.data_types.projects as projects

from nest_py.core.db.tablelike_sqla import TablelikeSqlaMaker
from nest_py.core.db.security_policy import SecurityPolicy

def setup_db():
    #these tests are detructive of the nest_users table in
    #the database, so point nest_users at a different table
    #for the duration of these tests
    nest_users.COLLECTION_NAME = 'test_users'
    md = nest_db.get_global_sqlalchemy_metadata()
    sqla_maker = core_db.get_nest_users_sqla_maker()
    users_tbl = sqla_maker.get_sqla_table(md)
    
    # initialize the test_projects db table
    projects.COLLECTION_NAME = 'test_projects'
    sp = SecurityPolicy(anyone_can_write=True, anyone_can_read_all=False)
    proj_sqla_maker = TablelikeSqlaMaker(projects.generate_schema(), security_policy=sp)
    proj_tbl = proj_sqla_maker.get_sqla_table(md)
    
    engine = nest_db.get_global_sqlalchemy_engine()
    if users_tbl.exists(engine):
        print('dropping existing table test_users')
        users_tbl.drop(engine)
    users_tbl.create(engine)
    print('created table test_users')
    
    # This is a side-effect of KNOW-516
    # TODO: Update this when fixing/moving db_ops_utils.ensure_default_project()
    if proj_tbl.exists(engine):
        print('dropping existing table test_projects')
        proj_tbl.drop(engine)
    proj_tbl.create(engine)
    print('created table test_projects')
    return

def make_users_db_client():
    md = nest_db.get_global_sqlalchemy_metadata()
    sqla_maker = core_db.get_nest_users_sqla_maker()
    engine = nest_db.get_global_sqlalchemy_engine()

    sys_user = core_db.get_system_user()
    db_client = sqla_maker.get_db_client(engine, md)
    db_client.set_requesting_user(sys_user)
    return db_client


def finish_up():

    #db_client = make_users_db_client()
    #db_client.delete_all_entries()

    nest_users.COLLECTION_NAME = 'nest_users'
    return

def test_add_system_user():
    setup_db()
    db_client = make_users_db_client()
    sys_user = core_db.get_system_user()
    db_client.delete_all_entries()

    sys_user_id = sys_user.get_nest_id()
    #create_entry doesn't allow the NestId to already be set
    #so this sort of hack must be done whenever the system_user is
    #created
    sys_user.set_nest_id(None)
    sys_user_tle = db_client.create_entry(sys_user.to_tablelike_entry())
    assert(not sys_user_tle is None)
    assert(sys_user_tle.get_nest_id() == sys_user_id)

    exp_id = core_db.SYSTEM_USER_NEST_ID
    print('exp_id: ' + str(exp_id))
    print('obs_id: ' + str(sys_user_tle.get_nest_id()))
    assert(sys_user_tle.get_nest_id() == exp_id)

    finish_up()
    return

def test_add_user_cli():
    setup_db()

    sys_user = core_db.get_system_user()
    sys_user.set_nest_id(None)
    users_client = make_users_db_client()
    sys_user_tle = users_client.create_entry(sys_user.to_tablelike_entry())

    nm = 'test_user0'
    pw = 'fake_pass'
    db_ops_utils.add_user(nm, pw)

    obs_tles = users_client.simple_filter_query({'username':nm})
    print(str(obs_tles))
    assert(len(obs_tles) == 1)
    finish_up()
    return

