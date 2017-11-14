from nest_py.core.db.tablelike_sqla import TablelikeSqlaMaker
from nest_py.core.db.sqla_maker import SqlaMaker
from nest_py.core.db.security_policy import SecurityPolicy
import nest_py.core.db.core_db as core_db 
import nest_py.core.data_types.nest_user as nest_users
import nest_py.knoweng.data_types.knoweng_schemas as knoweng_schemas

def get_sqla_makers():
    """
    get a lookup table of the SqlaMakers for the knoweng project.
    returns a dict of (name(str) -> SqlaMaker)
    """
    registry = dict()
    schemas = knoweng_schemas.get_schemas()
    security_policies = get_security_policies()
    for schema in schemas.values():
        nm = schema.get_name()
        sp = security_policies[nm]
        sqla_maker = TablelikeSqlaMaker(schema, security_policy=sp)
        registry[nm] = sqla_maker
    
    users_nm = nest_users.COLLECTION_NAME
    users_sqlam = core_db.get_nest_users_sqla_maker()
    registry[users_nm] = users_sqlam

    return registry

def get_security_policies():
    registry = dict()
    collection_names = knoweng_schemas.get_schemas().keys()
    #init all policies as default
    for cn in collection_names:
        registry[cn] = SecurityPolicy()

    #for endpoints where anyone can read all of the entries
    for cn in ['analysis_networks', 'public_gene_sets', 'collections', 'species']:
        registry[cn] = SecurityPolicy(anyone_can_read_all=True)

    return registry

def register_sqla_bindings(sqla_metadata):
    """
    ensures the bindings of all tables used by the knoweng
    project to the input sqla metadata object.
    """
    for sqla_maker in get_sqla_makers().values():
        sqla_maker.get_sqla_table(sqla_metadata)
    return

