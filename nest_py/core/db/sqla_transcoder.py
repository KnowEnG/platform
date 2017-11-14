
class SqlaJsonTranscoder(object):
    """
    encodes/decodes a type of object to a "flat" json form, which matches
    the form needed by SQL tables supported by SQLAlchemy. In particular
    the form of insert().values(flat_data) in insertion queries and the
    form returned by query results that then needs to be transformed into
    a python object.
    """
    def object_to_flat_jdata(self, dto):
        """ 
        must be able to convert the object to a flat dictionary (to map
        to a relational table).  arrays of primitives are allowed, so long
        as the table in the database is of type ARRAY 
        """
        jdata = None
        raise Exception("Abstract Class. Not Implemented")
        return jdata

    def flat_jdata_to_object(self, jdata):
        dto = None
        raise Exception("Abstract Class. Not Implemented")
        return dto
