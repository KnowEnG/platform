from nest_py.core.flask.nest_endpoints.nest_endpoint_set import NestEndpointSet

import nest_py.omix.data_types.omix_schemas as omix_schemas
import nest_py.omix.db.omix_db as omix_db
from nest_py.core.flask.nest_endpoints.logging_endpoint import LoggingEndpoint
from nest_py.core.flask.nest_endpoints.sessions_endpoint import SessionsEndpoint
from nest_py.core.flask.nest_endpoints.status_endpoint import StatusEndpoint
import nest_py.core.flask.nest_endpoints.tablelike_endpoints as tablelike_endpoints

def get_nest_endpoints(db_engine, sqla_metadata, authenticator):

    all_endpoints = NestEndpointSet()

    status_endpoint = StatusEndpoint(authenticator)
    all_endpoints.add_endpoint(status_endpoint)

    logging_endpoint = LoggingEndpoint(authenticator)
    all_endpoints.add_endpoint(logging_endpoint)

    sessions_endpoint = SessionsEndpoint(authenticator)
    all_endpoints.add_endpoint(sessions_endpoint)

    db_client_registry = omix_db.get_sqla_makers()
    schema_registry = omix_schemas.get_schemas()

    for schema_name in schema_registry:
        db_cm = db_client_registry[schema_name]
        db_client = db_cm.get_db_client(db_engine, sqla_metadata)
        schema = schema_registry[schema_name]
        eps = tablelike_endpoints.generate_endpoints(
            schema, db_client, authenticator)
        all_endpoints.add_endpoint_set(eps)

    return all_endpoints
