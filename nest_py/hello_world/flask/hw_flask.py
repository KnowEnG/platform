from nest_py.core.flask.nest_endpoints.crud_endpoints import NestCrudEntryEndpoint
from nest_py.core.flask.nest_endpoints.crud_endpoints import NestCrudCollectionEndpoint
from nest_py.core.flask.nest_endpoints.nest_endpoint_set import NestEndpointSet

from nest_py.core.flask.nest_endpoints.logging_endpoint import LoggingEndpoint
from nest_py.core.flask.nest_endpoints.sessions_endpoint import SessionsEndpoint
from nest_py.hello_world.flask.simplest_endpoint import SimplestEndpoint
from nest_py.core.flask.nest_endpoints.status_endpoint import StatusEndpoint
from nest_py.core.flask.nest_endpoints.whoami_endpoint import WhoamiEndpoint
import nest_py.core.flask.nest_endpoints.tablelike_endpoints as tablelike_endpoints

from nest_py.hello_world.data_types.simplest_dto import SimplestDTOTranscoder

import nest_py.hello_world.data_types.simplest_dto as simplest_dto
import nest_py.hello_world.db.hw_db as hw_db
import nest_py.hello_world.data_types.hw_schemas as hw_schemas
import nest_py.hello_world.data_types.hello_tablelike_sub as hello_tablelike_sub
import nest_py.hello_world.flask.hello_tablelike_sub_endpoints as hello_tablelike_sub_endpoints

def get_nest_endpoints(db_engine, sqla_metadata, authenticator):

    endpoints = NestEndpointSet()

    db_registry = hw_db.get_sqla_makers()
    for schema in hw_schemas.get_schemas():
        name = schema.get_name()
        if name == hello_tablelike_sub.COLLECTION_NAME:
            eps = hello_tablelike_sub_endpoints.generate_endpoints(db_engine, \
                sqla_metadata, authenticator)
        else:
            db_cm = db_registry[name]
            db_client = db_cm.get_db_client(db_engine, sqla_metadata)
            eps = tablelike_endpoints.generate_endpoints(schema, \
                db_client, authenticator)
        endpoints.add_endpoint_set(eps)

    #below are all endpoints that are not standard CRUD
    #over tablelikes

    dummy_ep = SimplestEndpoint(authenticator)
    endpoints.add_endpoint(dummy_ep)

    simplest_dto_eps = make_simplest_dto_endpoints(db_engine, sqla_metadata, authenticator)
    endpoints.add_endpoint_set(simplest_dto_eps)

    whoami_endpoint = WhoamiEndpoint(authenticator)
    endpoints.add_endpoint(whoami_endpoint)

    status_endpoint = StatusEndpoint(authenticator)
    endpoints.add_endpoint(status_endpoint)

    logging_endpoint = LoggingEndpoint(authenticator)
    endpoints.add_endpoint(logging_endpoint)

    sessions_endpoint = SessionsEndpoint(authenticator)
    endpoints.add_endpoint(sessions_endpoint)

    return endpoints

def make_simplest_dto_endpoints(db_engine, sqla_metadata, authenticator):
    """
    authenticator (AuthenticationStrategy)
    """
    api_transcoder = SimplestDTOTranscoder()
    sqla_maker = hw_db._make_simplest_dto_sqla_maker()
    db_client = sqla_maker.get_db_client(db_engine, sqla_metadata)
    nest_name = simplest_dto.COLLECTION_NAME

    endpoint_set = NestEndpointSet()

    collection_ep = NestCrudCollectionEndpoint(nest_name, db_client, \
        api_transcoder, authenticator)
    endpoint_set.add_endpoint(collection_ep)

    entry_ep = NestCrudEntryEndpoint(nest_name, db_client, \
        api_transcoder, authenticator)
    endpoint_set.add_endpoint(entry_ep)

    return endpoint_set
