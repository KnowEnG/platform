from sqlalchemy import Column, Integer, String

import nest_py.core.db.nest_db as nest_db

from nest_py.core.db.sqla_transcoder import SqlaJsonTranscoder
from nest_py.core.api_clients.api_transcoder import ApiJsonTranscoder
from nest_py.core.db.nest_entry import NestEntryMixin

COLLECTION_NAME = 'simplest_dto'

class SimplestDTO(nest_db.get_global_sqlalchemy_base(), NestEntryMixin):
    """
    an object that only has a 'message' field
    """

    __tablename__ = COLLECTION_NAME

    #the 'id' and 'owner_id' are now provided by NestEntryMixin
    #id = Column(Integer, primary_key=True)
    #owner_id = Column(Integer)
    message = Column(String)

    def __eq__(self, other):
        if other is None:
            return False
        if not (self.message == other.message):
            return False
        if not (self.id == other.id):
            return False
        if not (self.owner_id == other.owner_id):
            return False
        return True

    def __ne__(self, other):
        #pylint: disable=unneeded-not
        return not self == other
        #pylint: enable=unneeded-not

    def __str__(self):
        s = 'SimplestDTO:[message=' + self.message + ']'
        return s

class SimplestDTOTranscoder(ApiJsonTranscoder, SqlaJsonTranscoder):
    
    def object_to_jdata(self, dto):
        jdata = dict()
        jdata['message'] = dto.message
        if not dto.owner_id is None:
            jdata['owner_id'] = dto.owner_id
        if not dto.id is None:
            jdata['_id'] = dto.id
        return jdata

    def jdata_to_object(self, jdata):
        msg = jdata['message']
        if 'owner_id' in jdata:
            owner_id = jdata['owner_id']
        else:
            owner_id = None
        if '_id' in jdata:
            nid = jdata['_id']
        else:
            nid = None
        simple_dto = SimplestDTO(id=nid, owner_id=owner_id, message=msg)
        return simple_dto

    def object_to_flat_jdata(self, dto):
        api_jdata = self.object_to_jdata(dto)
        if '_id' in api_jdata:
            api_jdata['id'] = api_jdata.pop('_id')
        return api_jdata

    def flat_jdata_to_object(self, flat_jdata):
        if 'id' in flat_jdata:
            flat_jdata['_id'] = flat_jdata['id']
        return self.jdata_to_object(flat_jdata)

