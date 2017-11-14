from nest_py.core.data_types.nest_user import NestUser
from nest_py.core.data_types.nest_id import NestId
from nest_py.core.db.security_policy import SecurityPolicy
from nest_py.core.db.tablelike_sqla import TablelikeSqlaMaker
import nest_py.core.data_types.nest_user as nest_users

#like 'root' user in linux, the system_user must always have
#a predictable user_id b/c it is used during initialization
#when the users' subsystem might not exist yet
#'1' is what postgres starts with when using a default
#primary-key-sequence to generate id's
SYSTEM_USER_NEST_ID = NestId(1)

def get_system_user():
    """
    get the NestUser that is the owner of all entries in 
    the nest_user collection (database table).
    """
    username = 'nest_system'
    passlib_hash = '???'
    given_name = 'System'
    family_name = 'User'
    origin = 'core'
    is_superuser = True
    user = NestUser(SYSTEM_USER_NEST_ID, username, given_name,
        family_name, passlib_hash=passlib_hash, origin=origin,
        is_superuser=is_superuser)
    return user

def get_nest_users_access_policy():
    #this policy essentially means only a superuser can write, and 
    #only the superusers will then be able to read the entries owned
    #by superusers
    sp = SecurityPolicy(anyone_can_write=False, 
        anyone_can_read_all=False)
    return sp

def get_nest_users_sqla_maker():
    schema = nest_users.generate_schema()
    sp = get_nest_users_access_policy()
    sqla_maker = TablelikeSqlaMaker(schema, security_policy=sp)
    return sqla_maker


