from nest_py.core.api_clients.crud_api_client import CrudApiClient
from nest_py.core.api_clients.api_client_maker import ApiClientMaker

class TablelikeApiClientMaker(ApiClientMaker):

    def __init__(self, tablelike_schema):
        self.schema = tablelike_schema
        name = self.schema.get_name()
        super(TablelikeApiClientMaker, self).__init__(name)
        return

    def get_crud_client(self, http_client):
        transcoder = self.schema
        collection_name = self.get_collection_name()
        client = CrudApiClient(http_client, collection_name, transcoder)
        return client

    def run_smoke_scripts(self, http_client, result_acc):
        name = self.schema.get_name()
        result_acc.add_report_line('Begin smoke tests: ' + name)
        crud_client = self.get_crud_client(http_client)
        run_entry_crud_ops(self.schema, crud_client, result_acc)
        result_acc.add_report_line('End smoke tests: ' + name)
        return

def run_entry_crud_ops(tablelike_schema, crud_client, result_acc):
    """
    performs basic smoke tests on a TablelikeEntry endpoint by using 
    TablelikeSchema's ability to generate semi-random examples 
    that match the schema.

    Also uses the generic CrudApiClient.
    Uploads example data, downloads it, and verifies the values.
    """

    tle0 = tablelike_schema.generate_example_entry()
    tle1 = tablelike_schema.generate_example_entry()
    tle2 = tablelike_schema.generate_example_entry()

    log('tle0 : ' + str(tle0))
    log('tle1 : ' + str(tle1))
    log('tle2 : ' + str(tle2))

    result_acc.add_report_line('done initiating example tablelike data for: ' + 
        tablelike_schema.get_name())

    if not verify_entry_roundtrip(crud_client, tle0, result_acc):
        return

    if not verify_entry_roundtrip(crud_client, tle1, result_acc):
        return
        
    if not verify_entry_roundtrip(crud_client, tle2, result_acc):
        return
    return

def verify_entry_roundtrip(crud_client, entryX, result_acc):
    """
    crud_client (CrudApiClient)
    entryX (TablelikeEntry)
    resultAcc (SmokeTestResult)

    returns True if everything went ok
    """
    entryXsv = crud_client.create_entry(entryX)
    result_acc.add_report_line("POSTED entry : " + str(entryXsv))
    if entryXsv is None:
        result_acc.add_report_line("create entry X failed")
        result_acc.set_success(False)
        return False
    nest_id_x = entryXsv.get_nest_id()

    entryX_rt = crud_client.read_entry(nest_id_x)
    if entryX_rt is None:
        result_acc.add_report_line("reading entry X back from server failed")
        result_acc.set_success(False)
        return False

    result_acc.add_report_line('attempting to delete the entry')
    deleted_id = crud_client.delete_entry(nest_id_x)
    if deleted_id is None:
        result_acc.add_report_line('deleting entry reported failure')
        return False

    #make sure that GET no longer returns anything for the nest_id 
    fetched_deleted_entry = crud_client.read_entry(nest_id_x, num_tries=1)
    if fetched_deleted_entry is None:
        result_acc.add_report_line('deleted entry is verified to be gone')
    else:
        result_acc.add_report_line('entry that was supposedly deleted returned a result')
        return False

    return True

def log(msg):
    print(msg)
        
        
