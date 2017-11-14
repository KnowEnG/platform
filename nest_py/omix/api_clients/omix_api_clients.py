import nest_py.omix.data_types.omix_schemas as omix_schemas
import nest_py.core.api_clients.smoke_scripts as smoke_scripts
from nest_py.core.api_clients.smoke_scripts import SmokeTestResult
from nest_py.core.api_clients.tablelike_api_client_maker import TablelikeApiClientMaker


def get_api_client_makers():
    client_makers = dict()
    schemas = omix_schemas.get_schemas().values()
    for schema in schemas:
        name = schema.get_name()
        cm = TablelikeApiClientMaker(schema)
        client_makers[name] = cm

    return client_makers

def run_all_smoke_tests(http_client):
    smoke_res = SmokeTestResult('omix')
    acms = get_api_client_makers().values()
    smoke_scripts.login_client(http_client, smoke_res)
    for acm in acms:
        acm.run_smoke_scripts(http_client, smoke_res)
    return smoke_res

