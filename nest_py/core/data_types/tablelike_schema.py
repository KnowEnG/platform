import itertools
import json
from nest_py.core.data_types.tablelike_entry import TablelikeEntry
from nest_py.core.data_types.nest_id import NestId
from nest_py.core.db.sqla_transcoder import SqlaJsonTranscoder
from nest_py.core.api_clients.api_transcoder import ApiJsonTranscoder

class TablelikeSchema(SqlaJsonTranscoder, ApiJsonTranscoder):
    """
    Definition of attributes of datapoints, similar to
    column names, types, and constraints you would see in
    a relational model.

    Used to generate json models on the server and client
    that are flat kvp entries.

    So a row in a table with columns "name" and "age" would
    end up as a json entry like:
     {
        "name":"Bob",
        "age": 37.5
     }

     This schema defines the key attributes, what their type
     is, and possibly a constraint on the range of values 
     that are allowed.
    """
    
    def __init__(self, collection_name):
        self.collection_name = collection_name

        #TODO: add a 'get_attribute_type()' to all the attribute 
        #subclasses so we can just have one list of all attributes.
        #this hasn't scaled well with lots of new types
        self.numeric_attributes = list()
        self.foreignid_attributes = list()
        self.json_attributes = list()
        self.categoric_attributes = list()
        self.boolean_attributes = list()
        self.int_attributes = list()
        self.numeric_list_attributes = list()
        self.categoric_list_attributes = list()
        self.foreignid_list_attributes = list()
        self.int_list_attributes = list()

        #entries are list of column names. each of those lists is
        #a group of columns to be indexed together in the database table
        self.indexes = list()
        return

    def get_name(self):
        return self.collection_name

    def add_numeric_attribute(self, att_name, min_val=None, max_val=None):
        att = NumericAttribute(att_name, min_val, max_val)
        self.numeric_attributes.append(att)
        return

    def add_categoric_attribute(self, att_name, valid_values=None):
        """
        """
        att = CategoricAttribute(att_name, valid_values)
        self.categoric_attributes.append(att)
        return

    def add_foreignid_attribute(self, att_name):
        """
        An attribute where the values are of type NestId, and refer to an entry
        in a different schema than this one.

        TODO: might be better if instead of att_name, took the name of the foreign type,
            so you would pass in 'otus' instead of 'otu_id' if this attribute 
            referenced a NestId in the otus table. We could then setup proper foreign keys
            in the DB, but I'm not sure what that gets us.

        """
        att = ForeignIdAttribute(att_name)
        self.foreignid_attributes.append(att)
        return

    def add_json_attribute(self, att_name):
        """
        an attribute that is nested python primitives (dict, list, str, 
        int, etc), but when saved to the database is serialized to a json
        string. When passed over the API, will just look like nested JSON
        """
        att = JsonAttribute(att_name)
        self.json_attributes.append(att)
        return

    def add_boolean_attribute(self, att_name):
        """
        """
        att = BooleanAttribute(att_name)
        self.boolean_attributes.append(att)
        return

    def add_int_attribute(self, att_name, min_val=None, max_val=None):
        att = IntAttribute(att_name, min_val, max_val)
        self.int_attributes.append(att)
        return

    def add_numeric_list_attribute(self, att_name, min_val=None, max_val=None,
        min_num_vals=None, max_num_vals=None):
        att = NumericListAttribute(att_name, min_val, max_val, 
            min_num_vals, max_num_vals)
        self.numeric_list_attributes.append(att)
        return

    def add_categoric_list_attribute(self, att_name, valid_values=None,
        min_num_vals=None, max_num_vals=None):
        """
        An attribute that is a list of strings. 
        min and max_num_vals are optional (int) limits to the number of
            elements in the list for any given TablelikeEntry
        valid_values (optional) is a whitelist of permitted strings 
            that can be in the lists
        """
        att = CategoricListAttribute(att_name, valid_values, 
            min_num_vals, max_num_vals) 
        self.categoric_list_attributes.append(att)
        return

    def add_foreignid_list_attribute(self, att_name, valid_values=None,
        min_num_vals=None, max_num_vals=None):
        """
        An attribute that is a list of strings. 
        min and max_num_vals are optional (int) limits to the number of
            elements in the list for any given TablelikeEntry
        valid_values (optional) is a whitelist of permitted strings 
            that can be in the lists
        """
        att = ForeignIdListAttribute(att_name, valid_values, 
            min_num_vals, max_num_vals) 
        self.foreignid_list_attributes.append(att)
        return

    def add_int_list_attribute(self, att_name, min_val=None, max_val=None,
        min_num_vals=None, max_num_vals=None):
        att = IntListAttribute(att_name, min_val, max_val, 
            min_num_vals, max_num_vals)
        self.int_list_attributes.append(att)
        return

    def add_index(self, list_of_attribute_names):
        """
        each call to this method adds a db index based on the fields that are
        in the list (attribute names are column names in the database that the
        index will be built on). 
        """
        self.indexes.append(list_of_attribute_names)
        return


#tablelike entries server/client
    def object_to_jdata(self, tablelike_entry):
        """ApiJsonTranscoder override"""
        jdata = dict()
        for att in self.get_all_attributes():
            att_name = att.get_name()
            if att_name in tablelike_entry.get_data_dict():
                att_jdata = att.extract_jdata_from_entry(tablelike_entry)
            else:
                att_jdata = None
            jdata[att_name] = att_jdata
        if tablelike_entry.get_nest_id() is None:
            jdata['_id'] = None
        else:
            jdata['_id'] = tablelike_entry.get_nest_id().get_value()
        return jdata

    def jdata_to_object(self, jdata_of_tablelike_entry):
        """ApiJsonTranscoder override"""
        tle = TablelikeEntry(self)
        for att in self.get_all_attributes():
            if att.get_name() in jdata_of_tablelike_entry:
                att.set_entry_value_from_jdata(jdata_of_tablelike_entry, tle)
        if '_id' in jdata_of_tablelike_entry:
            nid = NestId(jdata_of_tablelike_entry['_id'])
            tle.set_nest_id(nid)
        else:
            tle.set_nest_id(None)
        return tle

    def object_to_flat_jdata(self, tablelike_entry):
        """SqlaJsonTranscoder override"""
        jdata = dict()
        for att in self.get_all_attributes():
            att_name = att.get_name()
            if att_name in tablelike_entry.attributes:
                att_jdata = att.extract_flat_jdata_from_entry(tablelike_entry)
                jdata[att_name] = att_jdata
        if tablelike_entry.get_nest_id() is None:
            jdata['id'] = None
        else:
            jdata['id'] = tablelike_entry.get_nest_id().get_value()
        return jdata

    def flat_jdata_to_object(self, jdata_of_tablelike_entry):
        """SqlaJsonTranscoder override"""
        tle = TablelikeEntry(self)
        for att in self.get_all_attributes():
            if att.get_name() in jdata_of_tablelike_entry:
                att.set_entry_value_from_flat_jdata(jdata_of_tablelike_entry, tle)
        if 'id' in jdata_of_tablelike_entry:
            nid = NestId(jdata_of_tablelike_entry['id'])
            tle.set_nest_id(nid)
        else:
            tle.set_nest_id(None)
        return tle

    def get_all_attributes(self):
        all_atts = itertools.chain(
            self.numeric_attributes,
            self.categoric_attributes,
            self.foreignid_attributes,
            self.json_attributes,
            self.boolean_attributes,
            self.int_attributes,
            self.numeric_list_attributes,
            self.categoric_list_attributes,
            self.foreignid_list_attributes,
            self.int_list_attributes)
        return all_atts

    def generate_example_entry(self):
        tle = TablelikeEntry(self)
        for att in self.get_all_attributes():
            att_name = att.get_name()
            att_val = att.generate_example_value()
            tle.set_value(att_name, att_val)
        return tle

class NumericAttribute():

    def __init__(self, attribute_name, min_val, max_val):
        self.name = attribute_name
        self.min_val = min_val
        self.max_val = max_val
        return

    def get_name(self):
        return self.name

    def extract_jdata_from_entry(self, tablelike_entry):
        """
        extracts this attribute's value from a tablelike_entry
        and transforms it into a jdata value
        """
        raw = tablelike_entry.get_value(self.name)
        #ints will also get forced to floats
        jdata = float(raw)
        return jdata

    def extract_flat_jdata_from_entry(self, tablelike_entry):
        jdata = self.extract_jdata_from_entry(tablelike_entry)
        return jdata

    def set_entry_value_from_jdata(self, jdata, tablelike_entry):
        """
        extracts this attribute from a jdata representation
        and populates the input tablelike_entry's field with
        the value (in place). 

        returns None
        """
        val = float(jdata[self.name])
        tablelike_entry.set_value(self.name, val)
        return

    def set_entry_value_from_flat_jdata(self, jdata, tablelike_entry):
        self.set_entry_value_from_jdata(jdata, tablelike_entry)
        return

    def generate_example_value(self):
        example_val =  0.0
        if self.min_val is None:
            if self.max_val is None:
                example_val = 0.0
            else:
                example_val = self.max_val - 1.0
        else:
            if self.max_val is None:
                example_val = self.min_val + 1.0
            else:
                val_range = self.max_val - self.min_val
                mp = self.min_val + (val_range / 2.0)
                example_val = mp
        return example_val


class CategoricAttribute():

    def __init__(self, attribute_name, valid_values):
        self.name = attribute_name
        self.valid_values = valid_values
        return

    def get_name(self):
        return self.name


    def extract_jdata_from_entry(self, tablelike_entry):
        """
        extracts this attribute's value from a tablelike_entry
        and transforms it into a jdata value
        """
        val = tablelike_entry.get_value(self.name)
        jdata = val
        return jdata

    def extract_flat_jdata_from_entry(self, tablelike_entry):
        jdata = self.extract_jdata_from_entry(tablelike_entry)
        return jdata

    def set_entry_value_from_flat_jdata(self, jdata, tablelike_entry):
        self.set_entry_value_from_jdata(jdata, tablelike_entry)
        return

    def set_entry_value_from_jdata(self, jdata, tablelike_entry):
        """
        extracts this attribute from a jdata representation
        and populates the input tablelike_entry's field with
        the value (in place). 

        returns None
        """
        val = jdata[self.name]
        tablelike_entry.set_value(self.name, val)
        return

    def generate_example_value(self):
        if self.valid_values is None:
            example_val = "example_val_0"
        else:
            example_val = self.valid_values[0]
        return example_val

class CategoricListAttribute():

    def __init__(self, attribute_name, valid_values, min_num_vals,
        max_num_vals):
        self.name = attribute_name
        self.valid_values = valid_values
        self.min_num_vals = min_num_vals
        self.max_num_vals = max_num_vals
        return

    def get_name(self):
        return self.name

    def extract_jdata_from_entry(self, tablelike_entry):
        """
        extracts this attribute's value from a tablelike_entry
        and transforms it into a jdata value
        """
        list_of_strings = tablelike_entry.get_value(self.name)
        #list of strings already valid jdata
        return list_of_strings

    def extract_flat_jdata_from_entry(self, tablelike_entry):
        jdata = self.extract_jdata_from_entry(tablelike_entry)
        return jdata

    def set_entry_value_from_jdata(self, jdata, tablelike_entry):
        """
        extracts this attribute from a jdata representation
        and populates the input tablelike_entry's field with
        the value (in place). 

        returns None
        """
        val = [str(x) for x in jdata[self.name]]
        tablelike_entry.set_value(self.name, val)
        return

    def set_entry_value_from_flat_jdata(self, jdata, tablelike_entry):
        self.set_entry_value_from_jdata(jdata, tablelike_entry)
        return

    def generate_example_value(self):
        if self.valid_values is None:
            example_val = "example_val_0"
        else:
            example_val = self.valid_values[0]
        return [example_val]

class NumericListAttribute():

    def __init__(self, attribute_name, min_val, max_val, min_num_vals,
        max_num_vals):
        self.name = attribute_name
        self.min_val = min_val
        self.max_val = max_val
        self.min_num_vals = min_num_vals
        self.max_num_vals = max_num_vals
        return

    def get_name(self):
        return self.name

    def extract_jdata_from_entry(self, tablelike_entry):
        """
        extracts this attribute's value from a tablelike_entry
        and transforms it into a jdata value
        """
        list_of_numbers = tablelike_entry.get_value(self.name)
        list_of_floats = map(float, list_of_numbers)
        return list_of_floats

    def extract_flat_jdata_from_entry(self, tablelike_entry):
        jdata = self.extract_jdata_from_entry(tablelike_entry)
        return jdata

    def set_entry_value_from_jdata(self, jdata, tablelike_entry):
        """
        extracts this attribute from a jdata representation
        and populates the input tablelike_entry's field with
        the value (in place). 

        returns None
        """
        val = [float(x) for x in jdata[self.name]]
        tablelike_entry.set_value(self.name, val)
        return

    def set_entry_value_from_flat_jdata(self, jdata, tablelike_entry):
        self.set_entry_value_from_jdata(jdata, tablelike_entry)
        return

    def generate_example_value(self):
        example_val =  0.0
        if self.min_val is None:
            if self.max_val is None:
                example_val = 0.0
            else:
                example_val = self.max_val - 1.0
        else:
            if self.max_val is None:
                example_val = self.min_val + 1.0
            else:
                val_range = self.max_val - self.min_val
                mp = self.min_val + (val_range / 2.0)
                example_val = mp
        return [example_val]

class ForeignIdAttribute():

    def __init__(self, attribute_name ):
        self.name = attribute_name
        return

    def get_name(self):
        return self.name

    def extract_jdata_from_entry(self, tablelike_entry):
        """
        extracts this attribute's value from a tablelike_entry
        and transforms it into a jdata value
        """
        nest_id = tablelike_entry.get_value(self.name)
        jdata = nest_id.to_jdata()
        return jdata

    def extract_flat_jdata_from_entry(self, tablelike_entry):
        jdata = self.extract_jdata_from_entry(tablelike_entry)
        return jdata

    def set_entry_value_from_flat_jdata(self, jdata, tablelike_entry):
        self.set_entry_value_from_jdata(jdata, tablelike_entry)
        return

    def set_entry_value_from_jdata(self, jdata, tablelike_entry):
        """
        extracts this attribute from a jdata representation
        and populates the input tablelike_entry's field with
        the value (in place). 

        returns None
        """
        val = NestId(jdata[self.name])
        tablelike_entry.set_value(self.name, val)
        return

    def generate_example_value(self):
        example_val = NestId(0)
        return example_val

class ForeignIdListAttribute():

    def __init__(self, attribute_name, valid_values, min_num_vals,
        max_num_vals):
        self.name = attribute_name
        self.valid_values = valid_values
        self.min_num_vals = min_num_vals
        self.max_num_vals = max_num_vals
        return

    def get_name(self):
        return self.name

    def extract_jdata_from_entry(self, tablelike_entry):
        """
        extracts this attribute's value from a tablelike_entry
        and transforms it into a jdata value
        """
        list_of_nest_ids = tablelike_entry.get_value(self.name)
        list_of_vals = list()
        for nest_id in list_of_nest_ids:
            list_of_vals.append(nest_id.to_jdata())
        return list_of_vals

    def extract_flat_jdata_from_entry(self, tablelike_entry):
        jdata = self.extract_jdata_from_entry(tablelike_entry)
        return jdata

    def set_entry_value_from_jdata(self, jdata, tablelike_entry):
        """
        extracts this attribute from a jdata representation
        and populates the input tablelike_entry's field with
        the value (in place). 

        returns None
        """
        val = [NestId(x) for x in jdata[self.name]]
        tablelike_entry.set_value(self.name, val)
        return

    def set_entry_value_from_flat_jdata(self, jdata, tablelike_entry):
        self.set_entry_value_from_jdata(jdata, tablelike_entry)
        return

    def generate_example_value(self):
        example_val = NestId(0)
        return [example_val]


class JsonAttribute():

    def __init__(self, attribute_name ):
        self.name = attribute_name
        return

    def get_name(self):
        return self.name

    def extract_jdata_from_entry(self, tablelike_entry):
        """
        extracts this attribute's value from a tablelike_entry
        and transforms it into a jdata value
        """
        jdata = tablelike_entry.get_value(self.name)
        return jdata

    def extract_flat_jdata_from_entry(self, tablelike_entry):
        """
        serializes the nested json of this entry into a string,
        which can then be written into a string column of the DB
        """
        jdata = self.extract_jdata_from_entry(tablelike_entry)
        json_str = json.dumps(jdata)
        return json_str

    def set_entry_value_from_flat_jdata(self, jdata, tablelike_entry):
        json_str = jdata[self.name]
        jdata = json.loads(json_str)
        tablelike_entry.set_value(self.name, jdata)
        return

    def set_entry_value_from_jdata(self, jdata, tablelike_entry):
        """
        extracts this attribute from a jdata representation
        and populates the input tablelike_entry's field with
        the value (in place). 

        returns None
        """
        val = jdata[self.name]
        tablelike_entry.set_value(self.name, val)
        return

    def generate_example_value(self):
        example_val = {
            'l1':['a', 'b'],
            'd2':{ 'x': 1, 'y': 2.2, 'z': True }
        }
        return example_val

class BooleanAttribute():

    def __init__(self, attribute_name):
        self.name = attribute_name
        return

    def get_name(self):
        return self.name

    def extract_jdata_from_entry(self, tablelike_entry):
        """
        extracts this attribute's value from a tablelike_entry
        and transforms it into a jdata value
        """
        val = tablelike_entry.get_value(self.name)
        jdata = bool(val)
        return jdata

    def extract_flat_jdata_from_entry(self, tablelike_entry):
        jdata = self.extract_jdata_from_entry(tablelike_entry)
        return jdata

    def set_entry_value_from_flat_jdata(self, jdata, tablelike_entry):
        self.set_entry_value_from_jdata(jdata, tablelike_entry)
        return

    def set_entry_value_from_jdata(self, jdata, tablelike_entry):
        """
        extracts this attribute from a jdata representation
        and populates the input tablelike_entry's field with
        the value (in place). 

        returns None
        """
        val = bool(jdata[self.name])
        tablelike_entry.set_value(self.name, val)
        return

    def generate_example_value(self):
        example_val = True
        return example_val


class IntAttribute():

    def __init__(self, attribute_name, min_val, max_val):
        self.name = attribute_name
        self.min_val = min_val
        self.max_val = max_val
        return

    def get_name(self):
        return self.name

    def extract_jdata_from_entry(self, tablelike_entry):
        """
        extracts this attribute's value from a tablelike_entry
        and transforms it into a jdata value
        """
        raw = tablelike_entry.get_value(self.name)
        jdata = int(raw)
        return jdata

    def extract_flat_jdata_from_entry(self, tablelike_entry):
        jdata = self.extract_jdata_from_entry(tablelike_entry)
        return jdata

    def set_entry_value_from_jdata(self, jdata, tablelike_entry):
        """
        extracts this attribute from a jdata representation
        and populates the input tablelike_entry's field with
        the value (in place). 

        returns None
        """
        val = int(jdata[self.name])
        tablelike_entry.set_value(self.name, val)
        return

    def set_entry_value_from_flat_jdata(self, jdata, tablelike_entry):
        self.set_entry_value_from_jdata(jdata, tablelike_entry)
        return

    def generate_example_value(self):
        example_val =  0
        if self.min_val is None:
            if self.max_val is None:
                example_val = 0
            else:
                example_val = self.max_val - 1
        else:
            if self.max_val is None:
                example_val = self.min_val + 1
            else:
                val_range = self.max_val - self.min_val
                mp = self.min_val + (val_range / 2)
                example_val = int(mp)
        return example_val

class IntListAttribute():

    def __init__(self, attribute_name, min_val, max_val, min_num_vals,
        max_num_vals):
        self.name = attribute_name
        self.min_val = min_val
        self.max_val = max_val
        self.min_num_vals = min_num_vals
        self.max_num_vals = max_num_vals
        return

    def get_name(self):
        return self.name

    def extract_jdata_from_entry(self, tablelike_entry):
        """
        extracts this attribute's value from a tablelike_entry
        and transforms it into a jdata value
        """
        list_of_numbers = tablelike_entry.get_value(self.name)
        list_of_ints = map(int, list_of_numbers)
        return list_of_ints

    def extract_flat_jdata_from_entry(self, tablelike_entry):
        jdata = self.extract_jdata_from_entry(tablelike_entry)
        return jdata

    def set_entry_value_from_jdata(self, jdata, tablelike_entry):
        """
        extracts this attribute from a jdata representation
        and populates the input tablelike_entry's field with
        the value (in place). 

        returns None
        """
        val = [int(x) for x in jdata[self.name]]
        tablelike_entry.set_value(self.name, val)
        return

    def set_entry_value_from_flat_jdata(self, jdata, tablelike_entry):
        self.set_entry_value_from_jdata(jdata, tablelike_entry)
        return

    def generate_example_value(self):
        example_val =  0
        if self.min_val is None:
            if self.max_val is None:
                example_val = 0
            else:
                example_val = self.max_val - 1
        else:
            if self.max_val is None:
                example_val = self.min_val + 1
            else:
                val_range = self.max_val - self.min_val
                mp = self.min_val + (val_range / 2)
                example_val = int(mp)
        return [example_val]


