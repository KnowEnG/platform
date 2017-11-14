"""
Represent a single tornado run. Only samples from the same tornado run
are comparable.
"""

from nest_py.core.data_types.tablelike_schema import TablelikeSchema

COLLECTION_NAME = 'tornado_runs'

def generate_schema():
    schema = TablelikeSchema(COLLECTION_NAME)
    schema.add_categoric_attribute('date_of_run', valid_values=None)
    schema.add_categoric_attribute('display_name_short', valid_values=None)
    schema.add_numeric_attribute('num_samples', min_val=0, max_val=None)
    schema.add_numeric_attribute('num_otus', min_val=0, max_val=None)
    return schema

