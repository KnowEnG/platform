"""
hello_world example of building a tablelike schema which
then has a batch endpoint, client, and smoke tests.
"""

from nest_py.core.data_types.tablelike_schema import TablelikeSchema
from nest_py.core.data_types.tablelike_entry import TablelikeEntry

COLLECTION_NAME = 'hello_tablelike'

def generate_schema():
    """
    This is the main, global defintion for the data type 'hello_tablelike'.
    From this definition we can generate Eve configurations for server
    endpoints that read/write the data, a python client for working with
    batches of tablelike_entries that conform to this schema and talk to the
    server, and auto generated smoke tests that exercise the endpoints with
    randomly generated data.
    """
    schema = TablelikeSchema(COLLECTION_NAME)
    schema.add_numeric_attribute('flt_val_0', min_val=0.0, max_val=None)
    schema.add_numeric_attribute('flt_val_1', min_val=-10.0, max_val=10.0)
    schema.add_categoric_attribute('string_val', valid_values=['x','y','z'])
    schema.add_categoric_list_attribute('cat_list_val', valid_values=['a','b','c'])
    schema.add_numeric_list_attribute('num_list_val')
    schema.add_foreignid_attribute('foreignid_val')
    schema.add_foreignid_list_attribute('foreignid_list_val')
    schema.add_json_attribute('json_val')
    schema.add_int_attribute('int_val')
    schema.add_int_list_attribute('int_list_val')

    schema.add_index(['string_val'])
    schema.add_index(['string_val', 'int_val'])
    return schema

class HelloTablelikeDTO(object):
    """
    example of a dto that maps directly to TablelikeEntry.

    Note that in some (many?) cases, the DTO might not be worth building.
    For instance, if scanning a csv file and uploading the rows as entries
    with little modification, just defining a schema and creating
    TablelikeEntry objects directly would be sufficient.
    """

    def __init__(self, flt_val_0, flt_val_1, string_val_0, cat_list, 
        num_list, foreignid, foreignid_list, jdata_0, int_0, int_list):
        self.flt_val_0 = flt_val_0
        self.flt_val_1 = flt_val_1
        self.string_val = string_val_0
        self.cat_list = cat_list
        self.num_list = num_list
        self.foreignid = foreignid
        self.foreignid_list = foreignid_list
        self.jdata_0 = jdata_0
        self.int_0 = int_0
        self.int_list = int_list
        return
    
    def to_tablelike_entry(self):
        """
        convert this DTO into a TablelikeEntry, using
        the TablelikeSchema from generate_schema()
        """
        tablelike_schema = generate_schema()
        tle = TablelikeEntry(tablelike_schema)
        tle.set_value('flt_val_0', self.flt_val_0)
        tle.set_value('flt_val_1', self.flt_val_1)
        tle.set_value('string_val', self.string_val)
        tle.set_value('cat_list_val', self.cat_list)
        tle.set_value('num_list_val', self.num_list)
        tle.set_value('foreignid_val', self.foreignid)
        tle.set_value('foreignid_list_val', self.foreignid_list)
        tle.set_value('json_val', self.jdata_0)
        tle.set_value('int_val', self.int_0)
        tle.set_value('int_list_val', self.int_list)
        return tle

    @staticmethod
    def from_tablelike_entry(entry):
        f0 = entry.get_value('flt_val_0')
        f1 = entry.get_value('flt_val_1')
        s = entry.get_value('string_val')
        cl = entry.get_value('cat_list_val')
        nl = entry.get_value('num_list_val')
        fi = entry.get_value('foreignid_val')
        fl = entry.get_value('foreignid_list_val')
        jd = entry.get_value('json_val')
        ind = entry.get_value('int_val')
        inl = entry.get_value('int_list_val')
        hello_tle = HelloTablelikeDTO(f0, f1, s, cl, nl, fi, fl, jd, ind, inl)
        return hello_tle

