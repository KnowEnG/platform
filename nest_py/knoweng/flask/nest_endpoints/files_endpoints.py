"""This module defines a set of hooks for the file endpoint.
"""
import os
import flask
from werkzeug.exceptions import UnsupportedMediaType, RequestEntityTooLarge
from werkzeug.utils import secure_filename

import nest_py.knoweng.data_types.files as files
from nest_py.knoweng.data_types.files import FileDTO
from nest_py.core.flask.nest_endpoints.crud_endpoints import NestCrudEntryEndpoint
from nest_py.core.flask.nest_endpoints.crud_endpoints import NestCrudCollectionEndpoint
from nest_py.core.flask.nest_endpoints.nest_endpoint_set import NestEndpointSet
from nest_py.core.data_types.tablelike_entry import TablelikeEntry
from nest_py.core.data_types.nest_id import NestId
from nest_py.core.data_types.nest_date import NestDate

def get_endpoint_set(files_db_client, authenticator):

    rel_url = files.COLLECTION_NAME
    files_schema = files.generate_schema()

    collection_ep = FileCollectionEndpoint(rel_url, files_db_client, \
        files_schema, authenticator)
    entry_ep = NestCrudEntryEndpoint(rel_url, files_db_client, \
        files_schema, authenticator)

    eps = NestEndpointSet()
    eps.add_endpoint(collection_ep)
    eps.add_endpoint(entry_ep)
    return eps

def _file_is_binary(file_storage):
    """
    Given a FileStorage object from an upload request, tests whether
    it contains non-ascii characters.

    Method comes from https://stackoverflow.com/a/7392391.

    Args:
        file_storage (werkzeug.datastructures.FileStorage): A FileStorage object
            from an upload request.

    Returns:
        bool: True if non-ascii bytes are found, else False.


    """
    textchars = bytearray(\
        {7, 8, 9, 10, 12, 13, 27} | set(range(0x20, 0x100)) - {0x7f})

    found_binary = False
    while not found_binary:
        block = file_storage.read(1024*1024)
        if len(block) == 0:
            # EOF
            break
        found_binary = bool(block.translate(None, textchars))
    file_storage.seek(0) # reset position
    return found_binary

def _readable_file_size(file_size):
    """Format the raw file size into human readable form.

    Args:
        file_size: number of bytes

    Returns:
        human reable file size in KB, MB etc.
    """
    for prefix in ['Bytes', 'KB', 'MB', 'GB', 'TB']:
        if file_size > 1.0 and file_size < 1024.0:
            return '%3.1f %s' % (file_size, prefix)
        file_size /= 1024.0

class FileCollectionEndpoint(NestCrudCollectionEndpoint):
    """Defines pre/post processing for file endpoint POST."""

    def __init__(self, rel_url, crud_db_client, files_schema, authenticator):

        super(FileCollectionEndpoint, self).__init__(
            rel_url, crud_db_client, files_schema, authenticator)

        config = flask.current_app.config

        self.userfiles_dir = config['USERFILES_DIR']
        self.files_schema = files_schema
        return

    def do_POST(self, request, requesting_user):
        """Handle new file upload by storing on the filesystem instead of
        storing in the database.

        TODO: Might
        also want a two-POST upload process: one POST to blob store, and a
        second POST on success to register the upload with Eve. Before any of
        that, though, need better understanding of long-term requirements.

        Args:
            request (flask.request): The request object.
        """
        # determine request properties
        has_multipart_header = 'multipart/form-data' in request.headers['Content-Type']
        is_too_big = False
        try:
            has_files_key = request.files.has_key('file')
        except RequestEntityTooLarge:
            is_too_big = True

        # handle request according to properties
        if is_too_big:
            # TODO revisit this case, but also all of the other limits enforced
            # here and in jobs_endpoints, when requirements for different user
            # types are better understood

            # How to handle this? Well, the official HTTP status code for this
            # case is 413, so we could create a response with an error message
            # and the 413 code. The trouble is that in practice, the response
            # received by clients won't include the error message or anything
            # else in the response body, perhaps because on a 413, the
            # connection may be interrupted; see
            # https://stackoverflow.com/a/19459277.
            # What's worse, although the content will be absent, the
            # content-length header will still correspond to the length of the
            # message set here, a mismatch that some browsers will tolerate--
            # e.g., FF and Edge on Win10, in my limited testing--but others,
            # notably Chrome, will not.

            # So OK, what if we change the error code to 500--will the response
            # body arrive at the client then? Unfortunately, for reasons I don't
            # yet understand, it behaves just like the 413, content-length
            # mismatch and all. Maybe, when the RequestEntityTooLarge exception
            # is raised, some switch deep within flask is flipped, triggering
            # the connection interruption regardless of the final status code on
            # the response. A quick grep of the code didn't turn up anything,
            # and that's about all I have time for now.

            # The safe thing, then, seems to be using a zero-length message
            # here to avoid the content-length mismatch. Unfortunately, that
            # means jumping through some hoops to build a sufficiently
            # informative message on the client side.

            # TLDR: use an empty message here or Chrome acts up
            resp = flask.make_response('', 413)
        elif has_multipart_header and has_files_key:
        #the post was of a FileBytesDTO, process the file upload

            upload = request.files['file']
            filename = secure_filename(upload.filename)
            form_data = request.form.to_dict()

            # perform file checks:

            # === 1 === single file must be < MAX_CONTENT_LENGTH
            # this is enforced by flask using MAX_CONTENT_LENGTH from app.config
            # flask will raise the errors when calling
            # `request.files.has_key('file')` above, and the case is handled
            # above in the is_too_big branch, because if it's that big, we
            # don't care about has_multipart_header and has_files_key

            # === 2 === single user must have < MAX_FILES_TOTAL_BYTES_PER_USER
            # arguably, this should be checked after we've determined the size
            # of this file below, but doing it here simplifies the flow, spares
            # us the trouble of writing and deleting, and keeps us within
            # MAX_CONTENT_LENGTH of MAX_FILES_TOTAL_BYTES_PER_USER, which is
            # plenty close
            # get all of the user's other files
            file_tles = self.crud_client.simple_filter_query(\
                dict(), user=requesting_user)
            sizes = [int(tle.get_value('filesize')) for tle in file_tles]
            max_total = \
                flask.current_app.config['MAX_FILES_TOTAL_BYTES_PER_USER']
            if sum(sizes) > max_total:
                resp = self._make_error_response('The total size of your ' + \
                    'uploaded data exceeds ' + \
                    _readable_file_size(max_total) + '. Make room for new ' + \
                    'uploads by deleting previous uploads, or contact us ' + \
                    'about a premium account.')

            # === 3 === file must be ascii
            elif _file_is_binary(upload):
                resp = self._make_error_response('Your uploaded spreadsheet ' + \
                    'contains binary data. Spreadsheets must be plain-text, ' + \
                    'tab-separated files.')
            else:
                # save file to disk
                project_raw = form_data['project']
                project_id = NestId(int(project_raw))
                files_dir = files.files_dirpath(self.userfiles_dir, project_id)
                if not os.path.exists(files_dir):
                    os.makedirs(files_dir)
                original_path = os.path.join(files_dir, filename)
                upload.save(original_path)

                # extract file info to save to db
                statinfo = os.stat(original_path).st_size
                extension = os.path.splitext(original_path)[-1].lower()
                uploader_name = requesting_user.get_username()

                file_tle = TablelikeEntry(self.files_schema)
                file_tle.set_value('filesize', str(statinfo))
                file_tle.set_value('filetype', extension)
                file_tle.set_value('filename', filename)
                file_tle.set_value('project_id', project_id)
                file_tle.set_value('uploadername', uploader_name)
                file_tle.set_value('_created', NestDate.now().to_jdata())
                file_tle.set_value('notes', '')
                file_tle.set_value('favorite', False)

                #save to db crud_client
                file_tle = self.crud_client.create_entry(file_tle, user=requesting_user)
                if file_tle is None:
                    raise Exception('Problem writing DB entry')
                file_dto = FileDTO.from_tablelike_entry(file_tle)

                #The final DTO only knows about the correct, final location
                #the file should be, so what it says is the filepath
                #is where we move the file to
                target_path = file_dto.get_file_path(self.userfiles_dir)
                os.rename(original_path, target_path)

                resp_jdata = self.format_create_single_jdata(request, file_tle)
                resp = self._make_success_json_response(resp_jdata)
        else:
            if has_multipart_header or has_files_key:
                #if we only had one, it's an error
                raise UnsupportedMediaType(\
                    'expected multipart/form-data Content-Type; ' + \
                    'got ' + request.headers['Content-Type'])
            else:
                #treat as a normal tablelike entry upload, do
                #the normal tablelike POST
                resp = super(FileCollectionEndpoint, self).do_POST(
                    request, requesting_user)
        return resp
