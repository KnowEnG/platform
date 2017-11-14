from nest_py.core.db.tablelike_sqla import TablelikeSqlaMaker
from nest_py.core.db.sqla_maker import SqlaMaker
from nest_py.core.db.security_policy import SecurityPolicy
import nest_py.omix.data_types.omix_schemas as omix_schemas
import nest_py.core.db.core_db as core_db 
import nest_py.core.data_types.nest_user as nest_users

def get_sqla_makers():
    """
    get a lookup table of the SqlaMakers for the omix project.
    returns a dict of (name(str) -> SqlaMaker)
    """
    registry = dict()
    for schema in omix_schemas.get_schemas().values():
        sqla_maker = TablelikeSqlaMaker(schema)
        tbl_name = sqla_maker.get_table_name() 
        registry[tbl_name] = sqla_maker
 
    users_nm = nest_users.COLLECTION_NAME
    users_sqlam = core_db.get_nest_users_sqla_maker()
    registry[users_nm] = users_sqlam

    return registry
        
def register_sqla_bindings(sqla_metadata):
    """
    ensures the bindings of all tables used by the omix
    project to the input sqla metadata object.
    """
    for sqla_maker in get_sqla_makers().values():
        sqla_maker.get_sqla_table(sqla_metadata)
    return

