
class ApiJsonTranscoder(object):
    """
    encodes/decodes a type of object to a json form of 
    all python primitives (which can be serialized to json
    with json.dumps) 
    """
    def object_to_jdata(self, dto):
        """
        """
        jdata = None
        raise Exception("Abstract Class. Not Implemented")
        return jdata

    def jdata_to_object(self, jdata):
        dto = None
        raise Exception("Abstract Class. Not Implemented")
        return dto
