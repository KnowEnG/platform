import nest_py.hello_world.data_types.simplest_dto as simplest_dto
from nest_py.core.db.tablelike_sqla import TablelikeSqlaMaker
from nest_py.core.db.sqla_maker import SqlaMaker
from nest_py.core.db.security_policy import SecurityPolicy
import nest_py.hello_world.data_types.hw_schemas as hw_schemas

import nest_py.core.db.core_db as core_db 
import nest_py.core.data_types.nest_user as nest_users

def get_sqla_makers():
    """
    get a lookup table of the SqlaMakers for the hello_world project.
    returns a dict of (name(str) -> SqlaMaker)
    """
    registry = dict()
    for schema in hw_schemas.get_schemas():
        sqla_maker = TablelikeSqlaMaker(schema)
        tbl_name = sqla_maker.get_table_name() 
        registry[tbl_name] = sqla_maker

    simplest_dto_sqlam = _make_simplest_dto_sqla_maker()
    simplest_name = simplest_dto_sqlam.get_table_name()
    registry[simplest_name] = simplest_dto_sqlam

 
    users_nm = nest_users.COLLECTION_NAME
    users_sqlam = core_db.get_nest_users_sqla_maker()
    registry[users_nm] = users_sqlam

    return registry
        
def register_sqla_bindings(sqla_metadata):
    """
    ensures the bindings of all tables used by the hello_world
    project to the input sqla metadata object.
    """
    for sqla_maker in get_sqla_makers().values():
        sqla_maker.get_sqla_table(sqla_metadata)
    return

def _make_simplest_dto_sqla_maker():
    """
    Create an SqlaMaker for the SimplestDTO type. Because
    SimplestDTO does not use a tablelike schema, we build
    an sqlaMaker by providing a transcoder that converts to/from
    sqlalchemy values
    """
    transcoder = simplest_dto.SimplestDTOTranscoder()
    table_name = simplest_dto.COLLECTION_NAME
    sp = SecurityPolicy(anyone_can_write=True, anyone_can_read_all=False)
    sqla_maker = SqlaMaker(table_name, transcoder, security_policy=sp)
    return sqla_maker

