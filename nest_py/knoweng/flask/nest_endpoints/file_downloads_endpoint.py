import flask
import os
from nest_py.core.flask.nest_endpoints.nest_endpoint import NestEndpoint
from nest_py.core.data_types.nest_id import NestId
import nest_py.knoweng.data_types.files as files
from nest_py.knoweng.data_types.files import FileDTO

class FileDownloadsEndpoint(NestEndpoint):

    def __init__(self, files_db_client, authenticator):
        """
        """
        self.userfiles_dir = flask.current_app.config['USERFILES_DIR']
        self.files_db_client = files_db_client
        self.rel_url = 'file_downloads'
        super(FileDownloadsEndpoint, self).__init__(self.rel_url, authenticator)
        return

    def get_flask_rule(self):
        rule =  'file_downloads/<int:file_id>'
        return(rule)

    def get_flask_endpoint(self):
        return 'file_downloads'

    def do_GET(self, request, requesting_user, file_id):
        nid = NestId(file_id)
        file_tle = self.files_db_client.read_entry(nid, user=requesting_user)
        file_dto = FileDTO.from_tablelike_entry(file_tle)
        user_filename = file_dto.filename

        #TODO: location info on disk still not very well encapsulated
        #b/c flask wants the directory and file separately
        project_id = file_dto.project_id
        on_disk_dir = files.files_dirpath(self.userfiles_dir, project_id)
        on_disk_basename = file_dto.get_nest_id().to_slug()
        
        return flask.send_from_directory(on_disk_dir, on_disk_basename, 
            as_attachment=True, attachment_filename=user_filename)
