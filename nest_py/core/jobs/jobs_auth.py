#utils for working with api authentication. 
#pretty simple for now
from nest_py.core.data_types.nest_user import NestUser
import nest_py.core.db.nest_db as nest_db
import nest_py.core.db.core_db as core_db

def login_jobs_user(http_client, nest_username, nest_userpass):
    """
    logs into the http_client as the default user that jobs
    run under 
    """
    http_client.login(nest_username, nest_userpass)
    return

def set_db_user(db_client, nest_username):
    """
    db_client(CrudDbClient)
    nest_username(str)

    similar to 'logging in', sets the requesting_user for a
    database client to the standard user that jobs run under.

    Note this is a NestUser for Nest's data ownership model, this
    is not the postgres user that connects to postgres.
    """
    #FIXME: this is a user that is also hardcoded in flask_config,
    #but we are keeping the flask packages out of the jobs packages
    #so we cut and paste
    users_sqla_maker = core_db.get_nest_users_sqla_maker()
    db_engine = nest_db.get_global_sqlalchemy_engine()
    md = nest_db.get_global_sqlalchemy_metadata()
    users_client = users_sqla_maker.get_db_client(db_engine, md)
    users_client.set_requesting_user(core_db.get_system_user())

    user_tle = users_client.simple_filter_query({'username':nest_username})[0]
    jobs_user = NestUser.from_tablelike_entry(user_tle)
    db_client.set_requesting_user(jobs_user)
    return
