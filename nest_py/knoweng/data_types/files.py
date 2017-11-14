import os
from nest_py.core.data_types.tablelike_schema import TablelikeSchema
from nest_py.core.data_types.tablelike_entry import TablelikeEntry
import nest_py.knoweng.data_types.projects as projects

COLLECTION_NAME = 'files'

def generate_schema():
    schema = TablelikeSchema(COLLECTION_NAME)
    schema.add_foreignid_attribute('project_id')
    schema.add_categoric_attribute('filename')
    # TODO change filesize to an int; values are too large to store as current
    # numeric attribute (TOOL-398)
    schema.add_categoric_attribute('filesize')
    schema.add_categoric_attribute('filetype')
    schema.add_categoric_attribute('uploadername')
    schema.add_categoric_attribute('_created')
    schema.add_categoric_attribute('notes')
    schema.add_boolean_attribute('favorite')
    return schema 

class FileDTO(object):

    def __init__(self, project_id, filename, filesize,
        filetype, uploadername, created, notes, favorite,
        nest_id=None):
        self.project_id = project_id
        self.filename = filename
        self.filesize = filesize
        self.filetype = filetype
        self.uploadername = uploadername
        self.created = created
        self.notes = notes
        self.favorite = favorite
        self.nest_id = nest_id
        return
    
    def get_nest_id(self):
        return self.nest_id

    def set_nest_id(self, nest_id):
        self.nest_id = nest_id
        return

    def get_file_path(self, userfiles_dir):
        """
        the valid filepath for a file uploaded through the api.
        might not be correct for files generated by jobs (which
            can have their own naming conventions)
        """
        fp = full_file_path(userfiles_dir, self.project_id, self.nest_id)
        return fp

    def to_tablelike_entry(self):
        schema = generate_schema()
        tle = TablelikeEntry(schema)
        tle.set_value('project_id', self.project_id)
        tle.set_value('filename', self.filename)
        tle.set_value('filesize', self.filesize)
        tle.set_value('filetype', self.filetype)
        tle.set_value('uploadername', self.uploadername)
        tle.set_value('_created', self.created)
        tle.set_value('notes', self.notes)
        tle.set_value('favorite', self.favorite)
        tle.set_nest_id(self.nest_id)
        return tle

    @staticmethod
    def from_tablelike_entry(tle):
        fdto = FileDTO(
            tle.get_value('project_id'),
            tle.get_value('filename'),
            tle.get_value('filesize'),
            tle.get_value('filetype'),
            tle.get_value('uploadername'),
            tle.get_value('_created'),
            tle.get_value('notes'),
            tle.get_value('favorite'),
            )
            
        fdto.set_nest_id(tle.get_nest_id())
        return fdto

def files_dirpath(userfiles_dir, project_nest_id):
    project_dir = projects.project_dirpath(userfiles_dir, project_nest_id)
    files_path = os.path.join(project_dir, 'files')     
    return files_path
   
def full_file_path(userfiles_dir, project_nest_id, file_nest_id):
    files_dir = files_dirpath(userfiles_dir, project_nest_id)
    file_path = os.path.join(files_dir, file_nest_id.to_slug())
    return file_path 


class FileBytesDTO(object):
    """
    A container for an actual file to upload to a Nest server. 
    The files endpoint can receive this data in a POST and then
    return just the tablelike info in the schema (above) if that
    nest_id is used in a GET.
    """

    def __init__(self, project_id, filelike):
        """
        project_id (NestId)
        filelike (file-like)
        """
        self.project_id = project_id
        self.filelike = filelike
        self.nest_id = None
        return

    def get_project_id(self):
        return self.project_id

    def get_file(self):
        return self.filelike

    def set_nest_id(self, nest_id):
        """
        set by api client if/when the file is successfully uploaded
        """
        self.nest_id = nest_id
        return

    def get_nest_id(self):
        return self.nest_id

    def to_jdata(self):
        # filelike is part of the files_dict, not the jdata
        return {'project': self.project_id.get_value()}

    def to_files_dict(self):
        return {'file': self.filelike}

    def __str__(self):
        s = 'FileBytesDTO:[project_id=' + self.project_id + \
                ',filelike=' + self.filelike + ']'
        return s

    @staticmethod
    def from_jdata(jdata):
        # TODO reading from the API, we'll get the file name in jdata but
        # won't get the file data at all
        fdto = FileBytesDTO(jdata['project'], None)
        return fdto

