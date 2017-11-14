from sqlalchemy import Column, Integer, String
from nest_py.core.data_types.nest_id import NestId

class NestEntryMixin(object):

    
    id = Column(Integer, primary_key=True)
    owner_id = Column(Integer)

    def set_nest_id(self, nest_id):
        self.id = nest_id.get_value()

    def get_nest_id(self):
        return NestId(self.id)


