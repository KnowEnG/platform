"""

"""

from nest_py.core.data_types.tablelike_schema import TablelikeSchema

COLLECTION_NAME = 'species'

def generate_schema():
    schema = TablelikeSchema(COLLECTION_NAME )
    schema.add_categoric_attribute('species_number', valid_values=None)
    schema.add_categoric_attribute('short_latin_name', valid_values=None)
    schema.add_categoric_attribute('name', valid_values=None)
    schema.add_int_attribute('display_order', min_val=None, max_val=None)
    schema.add_categoric_attribute('group_name', valid_values=None)
    schema.add_boolean_attribute('selected_by_default')
    return schema

