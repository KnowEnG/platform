
class ApiClientMaker(object):
    
    def __init__(self, collection_name):
        self.name = collection_name
        return

    def get_collection_name(self):
        return self.name

    def get_crud_client(self, http_client):
        """
        returns nest_py.core.api_clients.crud_api_client.CrudApiClient
        """
        raise NotImplementedError('ApiClientMaker.get_crud_client() : '+
            str(self.get_collection_name()))
        return None

    def run_smoke_scripts(self, http_client, result_acc):
        result_acc.add_report_line("No smoke_tests for collection: " +
            str(self.get_collection_name()))
        return

          

