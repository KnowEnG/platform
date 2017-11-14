import os

from nest_py.core.data_types.tablelike_schema import TablelikeSchema
from nest_py.core.data_types.tablelike_entry import TablelikeEntry

COLLECTION_NAME = 'projects'

def generate_schema():
    schema = TablelikeSchema(COLLECTION_NAME)
    schema.add_categoric_attribute('name')
    return schema 

class ProjectDTO(object):

    def __init__(self, name, nest_id=None):
        self.name = name
        self.nest_id = nest_id
        return

    def set_nest_id(self, nest_id):
        self.nest_id = nest_id
        return

    def get_nest_id(self):
        return self.nest_id

    def get_dirpath(self, userfiles_dir):
        path = project_dirpath(userfiles_dir, self.nest_id)
        return path

    def to_tablelike_entry(self):
        schema = generate_schema()
        tle = TablelikeEntry(schema)
        tle.set_value('name', self.name)
        tle.set_nest_id(self.nest_id)
        return tle

    @staticmethod
    def from_tablelike_entry(tle):
        nm = tle.get_value('name')
        pdto = ProjectDTO(nm)
        nid = tle.get_nest_id()
        pdto.set_nest_id(nid)
        return pdto

def project_dirpath(userfiles_dir, project_nest_id):
    basedir = 'PROJ-'  + project_nest_id.to_slug()
    project_dir = os.path.join(userfiles_dir, basedir)
    return project_dir

