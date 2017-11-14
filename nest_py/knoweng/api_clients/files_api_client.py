import traceback
from nest_py.core.api_clients.api_client_maker import ApiClientMaker
from nest_py.core.api_clients.crud_api_client import CrudApiClient
import nest_py.core.api_clients.tablelike_api_client_maker as tablelike_api_client_maker
from nest_py.core.api_clients.tablelike_api_client_maker import TablelikeApiClientMaker

from nest_py.core.api_clients.http_client import NestHttpRequest
from nest_py.core.data_types.tablelike_entry import TablelikeEntry
from nest_py.core.data_types.nest_id import NestId

import nest_py.knoweng.data_types.files as files
import nest_py.knoweng.data_types.projects as projects
from nest_py.knoweng.data_types.files import FileBytesDTO

class FilesApiClientMaker(ApiClientMaker):

    def __init__(self):
        name = files.COLLECTION_NAME
        super(FilesApiClientMaker, self).__init__(name)
        return

    def get_crud_client(self, http_client):
        ac = FilesApiClient(http_client)
        return ac

    def run_smoke_scripts(self, http_client, result_acc):
        file_client = self.get_crud_client(http_client)
        schema = files.generate_schema()
        #run the standard CRUD smoke tests using just file attributes
        tablelike_api_client_maker.run_entry_crud_ops(
            schema, file_client, result_acc)
        #now the smoke test that uploads an actual file
        smoke_file_0(http_client, result_acc, file_client)
        return

class FilesApiClient(CrudApiClient):
    """
    has the standard CRUD methods for tablelike entries of the
    'files' schema, but also adds a POST that uploads an
    actual file, which the endpoint will use to 1) store the
    file on the server and 2) make a 'files' entry with that
    file's info (name, extension, file size, etc)
    """

    def __init__(self, http_client):
        api_transcoder = files.generate_schema()
        name = files.COLLECTION_NAME
        super(FilesApiClient, self).__init__(
            http_client, name, api_transcoder)
        return

    def response_of_upload_file(self, fb_dto, 
        timeout_secs=60.0, verbose_errors=True, num_tries=3):
        """
        fb_dto(FileBytesDTO)
        """
        jdata = fb_dto.to_jdata()
        files_dict = fb_dto.to_files_dict()
        request = NestHttpRequest(self.relative_url,
            op="POST",
            http_params={},
            data=jdata,
            files=files_dict,
            num_tries=num_tries,
            require_json=True,
            timeout_secs=timeout_secs)

        response = self.http_client.perform_request(
            request, verbose_errors=False)
        return response

    def upload_file(self, fb_dto, timeout_secs=60.0):
        """
        same as response_of_upload_file, but returns the
        fb_dto with nest-id on success and None on any failure
        """
        response = self.response_of_upload_file(fb_dto, 
            timeout_secs=timeout_secs)
        if response.did_succeed():
            try:
                jdata = response.get_data_payload_as_jdata()
                nest_id = NestId(jdata['created_id'])
                fb_dto.set_nest_id(nest_id)
            except Exception as e:
                traceback.print_exc()
                log("create_entry error transforming json data to object")
                log("Exception: " + str(e))
                fb_dto = None
        else:
            fb_dto = None
        return fb_dto
  


def smoke_file_0(http_client, result_acc, file_client):
    result_acc.add_report_line('BEGIN smoke_file_0()')
    project_schema = projects.generate_schema()
    project_client = TablelikeApiClientMaker(project_schema).get_crud_client(http_client)
    
    project_tle_0 = TablelikeEntry(project_schema)
    project_tle_0.set_value('name', 'smoke test project')

    project_tle_1 = project_client.create_entry(project_tle_0)
    project_nest_id = project_tle_1.get_nest_id()
    
    file_handle = open('/code_live/README.rst', 'rb')
    fb_0 = FileBytesDTO(project_nest_id, file_handle)

    fb_1 = file_client.upload_file(fb_0)
    if fb_1 is None:
        result_acc.set_success(False)
        result_acc.add_report_line("Failed to upload file")

    file_nest_id = fb_1.get_nest_id()
    #this is a tle with the file's attributes
    file_tle = file_client.read_entry(file_nest_id)
    result_acc.add_report_line('read created file tle: ' + str(file_tle))
    if file_tle is None:
        result_acc.set_success(False)

    project_deleted_id = project_client.delete_entry( project_nest_id)
    if project_deleted_id is None:
        result_acc.add_report_line("ERROR: couldn't delete project we just created")
        result_acc.set_success(False)
    else:
        result_acc.add_report_line("deleted project we just created: " + str(project_nest_id))

    file_deleted_id = file_client.delete_entry(file_nest_id)
    if file_deleted_id is None:
        result_acc.add_report_line("ERROR: couldn't delete file we just created")
        result_acc.set_success(False)
    else:
        result_acc.add_report_line("deleted file we just created: " + str(file_nest_id))
    result_acc.add_report_line('END smoke_file_0()')
    return

def log(msg):
    print(msg)
