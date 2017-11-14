"""
Common high level commands. Most can be called from nest_ops.
"""

import copy
from sqlalchemy.sql import update

import nest_py.core.db.nest_db as nest_db
import nest_py.core.db.core_db as core_db
import nest_py.core.nest_config  as nest_config
import nest_py.core.data_types.nest_user as nest_users
import nest_py.knoweng.data_types.projects as projects
import nest_py.core.flask.accounts.password_hash as password_hash

from nest_py.core.data_types.nest_user import NestUser
from nest_py.core.data_types.tablelike_entry import TablelikeEntry
from nest_py.core.db.security_policy import SecurityPolicy
from nest_py.knoweng.data_types.projects import ProjectDTO
from nest_py.core.db.tablelike_sqla import TablelikeSqlaMaker
from nest_py.nest_envs import ProjectEnv
from sqlalchemy.engine.reflection import Inspector

def check_db_connection():
    engine = nest_db.get_global_sqlalchemy_engine()
    md = nest_db.get_global_sqlalchemy_metadata()
    try:
        connection = engine.connect()
        qs = 'select 1'
        q = engine.execute(qs)
        obs = q.first()[0]
        if obs == 1:
            print("'Select 1' returned 1")
            connectable = True
        else:
            print("'Select 1' returned " + str(obs))
            connectable = False
    except Exception as e:
        print('Connecting to DB Failed. Exception: ' + str(e))
        connectable = False
    if not connectable:
        print('config was' + str(nest_db.GLOBAL_SQLA_RESOURCES.config))
    return connectable


def ensure_tables_in_db():
    engine = nest_db.get_global_sqlalchemy_engine()
    md = nest_db.get_global_sqlalchemy_metadata()
    for tbl in md.sorted_tables:
        if tbl.exists(engine):
            print(' exists : ' + str(tbl.name))
        else:
            tbl.create(engine)
            print(' CREATED: ' + str(tbl.name))
    return True

def drop_tables_in_db():
    engine = nest_db.get_global_sqlalchemy_engine()
    nest_db.get_global_sqlalchemy_base().metadata.drop_all(engine)
    return True

def list_tables_in_db():
    engine = nest_db.get_global_sqlalchemy_engine()
    qs = """
    select table_catalog, table_schema, table_name, table_type 
    from information_schema.tables 
    where table_schema not in ('pg_catalog', 'information_schema');
    """
    q = engine.execute(qs)
    tables = q.fetchall()
    print("tables from db:")
    if len(tables) == 0:
        print('   <None>')
    for i, tbl in enumerate(tables):
        (c, s, n, t) = tbl
        print(str(i) + '.')
        print('   name    :' +  str(n))
        print('   catalog :' + str(c))
        print('   type    :' + str(t))
        print('   schema  :' + str(s))
    return True

def list_metadata_tables():
    md = nest_db.get_global_sqlalchemy_metadata()
    print("sqlalchemy table bindings: ")
    for tbl in md.sorted_tables:
        print(' ' + str(tbl.name))
    return True

def seed_users(project_env, runlevel):
    """
    adds users declared in nest_config to the nest_users table
    if they don't already exist
    """

    db_client_maker = core_db.get_nest_users_sqla_maker()
    md = nest_db.get_global_sqlalchemy_metadata()
    engine = nest_db.get_global_sqlalchemy_engine()
    #note this is a tablelike client, not a NestUser client
    db_client = db_client_maker.get_db_client(engine, md)

    #needs a unique *instance* of system_user to act as 'owner' 
    #as we will alter the instance that we add to the table
    db_client.set_requesting_user(core_db.get_system_user())

    user_configs = nest_config.generate_seed_users(project_env, runlevel)
    
    success = _add_users_from_configs(db_client, user_configs)
    return success

def _add_users_from_configs(db_client, user_configs):
 
    success = True
    user_tles = list()
    schema = nest_users.generate_schema()
    _validate_user_configs(user_configs)
    for cfg in user_configs:
        tle = TablelikeEntry(schema)
        #really, we can get by with only a username and password
        tle.set_value('username', cfg['username'])
        tle.set_value('passlib_hash', cfg['passlib_hash'])

        tle.set_value('is_superuser', cfg.get('is_superuser', False))

        #these others can be None (will be null in the db)
        tle.set_value('given_name', cfg.get('given_name', None))
        tle.set_value('family_name', cfg.get('family_name', None))
        tle.set_value('thumb_url', cfg.get('thumb_url', None))
        tle.set_value('origin', cfg.get('origin', 'nest'))
        tle.set_value('external_id', cfg.get('external_id', None))

        user_tles.append(tle)

    #add the system user first so it gets user id '1'
    system_user = core_db.get_system_user()
    system_user.set_nest_id(None)
    sys_username = system_user.get_username()
    user_tles = [system_user.to_tablelike_entry()] + user_tles

    for tle in user_tles:
        nm = tle.get_value('username')
        existings = db_client.simple_filter_query({'username':nm})
        if len(existings) == 0:
            tle = db_client.create_entry(tle)
            if tle is None:
                print(' FAILURE creating user: ' + str(nm))
                success = False
            else:
                print(' Created :' + str(nm))
                ensure_default_project(NestUser.from_tablelike_entry(tle))
            #force the system user to have it's hardcoded id
            if nm == sys_username:
                conn = db_client.get_sqla_connection()
                tbl = db_client.sqla_table
                update_dict = {'id':core_db.SYSTEM_USER_NEST_ID.get_value()}
                stmt = update(tbl)
                stmt = stmt.where(tbl.c.username == sys_username)
                stmt = stmt.values(update_dict)
                conn.execute(stmt)
                conn.close()
        elif len(existings) == 1:
            existing_tle = copy.copy(existings[0])
            #check for equivalence using only the fields that should match
            existing_tle.set_nest_id(None)
            existing_tle.set_value('passlib_hash', None)
            tle.set_value('passlib_hash', None)
            
            if existing_tle == tle:
                print(' Exists: ' + str(nm))
                ensure_default_project(NestUser.from_tablelike_entry(existings[0]))
            else:
                print(' MISMATCH! (doing nothing): ')
                print('   existing :' + str(existing_tle))  
                print('   in config:  ' + str(tle))
                success = False
        else:
            print(' FAILURE: Two existing db entries for: ' + str(nm))
            success = False
    return success

def _validate_user_configs(user_configs):
    if user_configs is None:
        raise AttributeError('DEMO_AUTHENTICATION_ACCOUNTS cannot be None')
    if len(user_configs) == 0:
        raise AttributeError('DEMO_AUTHENTICATION_ACCOUNTS cannot be empty')
    for account in user_configs:
        for field in ['username', 'password', 'given_name', 'family_name']:
            if field not in account or len(account[field].strip()) == 0:
                raise AttributeError(field + ' cannot be empty')
            # TODO further constrain legal characters
        if ' ' in account['username']:
            raise AttributeError(\
                'username cannot contain spaces')
        if ' ' in account['password']:
            raise AttributeError(\
                'password cannot contain spaces')
        if not 'passlib_hash' in account:
            if 'password' in account:
                pw = account['password']
                passlib_hash = password_hash.compute_passlib_hash(pw)
            else:
                passlib_hash = 'NO LOGIN'
            account['passlib_hash'] = passlib_hash
    if len(set(account['username'] for account in user_configs)) !=\
        len(user_configs):
        raise AttributeError('usernames must be unique')
    return

def add_user(username, password):
    """
    leaves most fields blank except the username and password needed
    to login to the webapp. adds the user to the localhost instance.
    """

    db_client_maker = core_db.get_nest_users_sqla_maker()
    md = nest_db.get_global_sqlalchemy_metadata()
    engine = nest_db.get_global_sqlalchemy_engine()
    #note this is a tablelike client, not a NestUser client
    db_client = db_client_maker.get_db_client(engine, md)

    system_user = core_db.get_system_user()
    db_client.set_requesting_user(system_user)

    schema = nest_users.generate_schema()
    passlib_hash = password_hash.compute_passlib_hash(password)

    nu = NestUser(None, username, None, None, 
        is_superuser=False, passlib_hash=passlib_hash,
        origin='nest')

    tle = nu.to_tablelike_entry()
    tle = db_client.create_entry(tle)
    if tle is None:
        print('FAILURE ensuring user: ' + str(username))
        success = False
    else:
        print('ensured user: ' + str(username))
        success = True
        ensure_default_project(NestUser.from_tablelike_entry(tle))
    return success
    
# TODO: This method should probably be located somewhere else
def ensure_default_project(nest_user):
    # initialize the projects db client
    schema = projects.generate_schema()
    sp = SecurityPolicy(anyone_can_write=True, anyone_can_read_all=False)
    sqla_maker = TablelikeSqlaMaker(schema, security_policy=sp)
    
    db_engine = nest_db.get_global_sqlalchemy_engine()
    md = nest_db.get_global_sqlalchemy_metadata()
    
    inspector = Inspector.from_engine(db_engine)
    
    # Noop for non-knoweng projects
    if not 'projects' in inspector.get_table_names():
        print 'No projects table defined... skipping'
        return None

    projects_client = sqla_maker.get_db_client(db_engine, md)
    projects_client.set_requesting_user(nest_user)
    
    uname = nest_user.get_username()
    owner_id = nest_user.get_nest_id().get_value()
    default_project_name = "Default Project"
    fltr = {'name': default_project_name, 'owner_id': owner_id}
    existings = projects_client.simple_filter_query(fltr)
    if len(existings) == 0:
        #user hasn't accessed Nest before, create new default project
        new_default_project = ProjectDTO(default_project_name)
        raw_tle = new_default_project.to_tablelike_entry()
        default_project_tle = projects_client.create_entry(raw_tle)
        print(" Created: Default Project for user '" + uname + "'")
    elif len(existings) == 1:
        #found a valid record for this project in the DB 
        default_project_tle = existings[0]
        print(" Exists: Default Project for user '" + uname + "'")
    else:
        print(" WARNING: Multiple Default Projects detected for username '" + uname + "'")
        default_project_tle = existings[0]

    if default_project_tle is None:
        default_project = None
        print('FAILURE ensuring default project: ' + uname)
    else:
        default_project = ProjectDTO.from_tablelike_entry(default_project_tle)
        print('ensured default project: ' + uname)
        
    return default_project


