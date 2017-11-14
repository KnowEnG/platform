
class TablelikeEntry(object):
    """
    A single key-value-pairs entry that conforms to a tablelike schema
    """

    def __init__(self, tablelike_schema):
        self.attributes = dict()
        self.schema = tablelike_schema
        self.nest_id = None
        self.owner_id = None
        return

    def set_data_dict(self, data):
        self.attributes = data
        return

    def get_data_dict(self):
        return self.attributes

    def set_value(self, att_name, val):
        """
        att_name (string) name of attribute/column
        val (either string, float, NestId, jdata blob, or
        list of those, depending on schema)
        """
        #TODO: should we enforce the schema types here?
        self.attributes[att_name] = val
        return

    def get_value(self, att_name):
        """
        get the value of attribute named att_name

        att_name (string)

        """
        #TODO good error messages for not found or None
        value = self.attributes[att_name]
        return value

    def __eq__(self, other):
        verbose = False#for debugging
        if other is None:
            return False
        if not (len(self.attributes) == len(other.attributes)):
            if verbose:
                print("num atts don't match")
            return False
        for att_name in self.attributes:
            if not att_name in other.attributes:
                if verbose:
                    print('other is missing att: ' + att_name)
                return False
            if not self.attributes[att_name] == other.attributes[att_name]:
                if verbose:
                    print("'" + att_name + "' values don't match " +
                        str(self.attributes[att_name]) + ' != ' +
                        str(other.attributes[att_name]))
                return False
        if not self.nest_id == other.nest_id:
            if verbose:
                print("nest_ids don't match")
            return False
        if not self.owner_id == other.owner_id:
            if verbose:
                print("owner id's don't match")
            return False
        return True

    def __ne__(self, other):
        return (not self.__eq__(other))

    def get_nest_id(self):
        return self.nest_id

    def set_nest_id(self, nest_id):
        self.nest_id = nest_id
        return

    def get_owner_id(self):
        return self.owner_id

    def set_owner_id(self, owner_id):
        self.owner_id = owner_id
        return

    def get_schema(self):
        return self.schema

    def __str__(self):
        s = '{'
        s += str(self.nest_id) + '::'
        for att in self.attributes:
            s += str(att) + ':' + str(self.attributes[att]) + ', '
        s += '}'
        return s

