"""
Example of a Tablelike collection with side effects on the crud
operations implemented by subclassing the appropriate Endpoints.
"""

from nest_py.core.data_types.tablelike_schema import TablelikeSchema

COLLECTION_NAME = 'demo_sub'

def generate_schema():
    """
    A schema that will be given non-standard behavior in the
    api endpoints.
    """
    schema = TablelikeSchema(COLLECTION_NAME)
    schema.add_numeric_attribute('flt_val_0_sub', min_val=-10.0, max_val=10.0)
    schema.add_categoric_attribute('string_val_sub', valid_values=['x','y','z'])
    return schema


