from nest_py.core.flask.nest_endpoints.nest_endpoint_set import NestEndpointSet
from nest_py.core.flask.nest_endpoints.crud_endpoints import NestCrudEntryEndpoint
from nest_py.core.flask.nest_endpoints.crud_endpoints  import NestCrudCollectionEndpoint

def generate_endpoints(tablelike_schema, crud_db_client, authenticator):
    endpoint_set = NestEndpointSet()    
    transcoder = tablelike_schema
    relative_url_base = tablelike_schema.get_name()
    epc = NestCrudCollectionEndpoint(relative_url_base, 
        crud_db_client, transcoder, authenticator)
    endpoint_set.add_endpoint(epc)
    
    epe = NestCrudEntryEndpoint(relative_url_base, crud_db_client, 
        transcoder, authenticator)
    endpoint_set.add_endpoint(epe)
    return endpoint_set

