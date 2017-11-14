from nest_py.core.api_clients.tablelike_api_client_maker import TablelikeApiClientMaker

from nest_py.hello_world.api_clients.simplest_dto_api_client import SimplestDTOApiClientMaker

import nest_py.core.api_clients.smoke_scripts as smoke_scripts
from nest_py.core.api_clients.smoke_scripts import SmokeTestResult
import nest_py.hello_world.data_types.hw_schemas as hw_schemas

def get_api_client_makers():
    acms = dict()
    for schema in hw_schemas.get_schemas():
        name = schema.get_name()
        acm = TablelikeApiClientMaker(schema)
        acms[name] = acm

    #simplestDTO is not a tablelike type, has a custom client_maker
    acm = SimplestDTOApiClientMaker()
    name = acm.get_collection_name()
    acms[name] = acm

    return acms

def run_all_smoke_tests(http_client):
    """
    """
    result_acc = SmokeTestResult('hello_world')
    acms = get_api_client_makers()

    #simplestDTO has the login/authorization smoke test. run
    #that first, and if it fails, don't bother with the rest
    #since they can only generate redundant errors
    sdto_acm = acms.pop('simplest_dto')
    sdto_acm.run_smoke_scripts(http_client, result_acc)

    if result_acc.did_succeed():
        smoke_scripts.login_client(http_client, result_acc)
        for acm in acms.values():
            acm.run_smoke_scripts(http_client, result_acc)

    return result_acc


