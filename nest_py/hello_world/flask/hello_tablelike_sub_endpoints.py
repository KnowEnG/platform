
from nest_py.core.flask.nest_endpoints.crud_endpoints import NestCrudEntryEndpoint
from nest_py.core.flask.nest_endpoints.crud_endpoints import NestCrudCollectionEndpoint
from nest_py.core.flask.nest_endpoints.nest_endpoint_set import NestEndpointSet

import nest_py.hello_world.db.hw_db as hw_db
import nest_py.hello_world.data_types.hello_tablelike_sub as hello_tablelike_sub

def generate_endpoints(db_engine, sqla_metadata, authenticator):
    endpoint_set = NestEndpointSet()    
    #note that we are still using the standard way to build a 
    #db client for a tablelike schema, but we could also create a 
    #different one here if we wanted the database CRUD ops 
    #to work different
    coll_name = hello_tablelike_sub.COLLECTION_NAME
    db_client_maker = hw_db.get_sqla_makers()[coll_name]
    db_client = db_client_maker.get_db_client(db_engine, sqla_metadata)
    schema = hello_tablelike_sub.generate_schema()
    relative_url_base = schema.get_name()
    transcoder = schema
    epc = SubCollectionEndpoint(relative_url_base, 
        db_client, transcoder, authenticator)
    endpoint_set.add_endpoint(epc)
    
    epe = SubEntryEndpoint(relative_url_base, db_client, 
        transcoder, authenticator)
    endpoint_set.add_endpoint(epe)
    return endpoint_set

class SubEntryEndpoint(NestCrudEntryEndpoint):
    """
    Example of how to make a new "CrudEntry" endpoint, which
    is the one where you can GET, PATCH, or DELETE a single
    entry at the url with the id attached (e.g. api/<data_type>/<id>) 
    """
    def do_GET(self, request, requesting_user, nid_int):
        print("hello from 'demo_sub' before we do a GET on an entry: " + str(nid_int))
        resp = super(SubEntryEndpoint, self).do_GET(request, requesting_user, nid_int)
        print("hello from 'demo_sub' after we do a GET on an entry, " +
            "but before we return the response")
        return resp

class SubCollectionEndpoint(NestCrudCollectionEndpoint):
    """
    Example of how to make a new "CrudCollection" endpoint, which
    is the one where you can POST a new entry and GET a list
    of entries that match a query. eg. api/<data_type>?p1=v1
    """

    def do_POST(self, request, requesting_user):
        print("hello from 'demo_sub' before we do a POST a new entry " +
            "to the collection endpoint")
        resp = super(SubCollectionEndpoint, self).do_POST(request, requesting_user)
        print("hello from 'demo_sub' after we POST a new entry, " +
            "and have saved it to the database, but before we return " +
            "the response")
        return resp

