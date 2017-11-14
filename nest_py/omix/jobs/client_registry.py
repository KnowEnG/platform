import nest_py.omix.api_clients.omix_api_clients as omix_api_clients
import nest_py.omix.db.omix_db as omix_db

def make_api_client_registry(http_client):
    """
    makes a dictionary from collection_name(str) -> api_client
    """
    registry = dict()
    for client_maker in omix_api_clients.get_api_client_makers().values():
        name = client_maker.get_collection_name()
        client = client_maker.get_crud_client(http_client)
        registry[name] = client
        print('Registering API CRUD client: ' + name)

    return registry

def make_db_client_registry(db_engine, sqla_metadata):
    registry = dict()
    for client_maker in omix_db.get_sqla_makers().values():
        name = client_maker.get_table_name()
        client = client_maker.get_db_client(db_engine, sqla_metadata)
        registry[name] = client
        print('Registering DB CRUD client: ' + name)
    return registry
