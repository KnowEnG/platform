"""
Observations of a Feature Variable. "Realization" like the
realization of a random variable:
https://en.wikipedia.org/wiki/Realization_(probability)

The types of data that can be stored as realizations must
be able to map directly into numpy arrays for use with
sklearn, pandas, etc. 
"""

from nest_py.core.data_types.tablelike_schema import TablelikeSchema
from nest_py.core.data_types.tablelike_entry import TablelikeEntry

NUMERIC_COLLECTION_NAME = 'realizations_numeric'
def generate_schema_numeric():

    schema = TablelikeSchema(NUMERIC_COLLECTION_NAME)
    schema.add_foreignid_attribute('feature_variable_id')
    schema.add_foreignid_attribute('subject_id')
    schema.add_foreignid_attribute('data_batch_id')
    schema.add_foreignid_attribute('wix_run_id')
    schema.add_numeric_attribute('float_value')
    return schema


CATEGORIC_COLLECTION_NAME = 'realizations_categoric'
def generate_schema_categoric():
    schema = TablelikeSchema(CATEGORIC_COLLECTION_NAME)
    schema.add_foreignid_attribute('feature_variable_id')
    schema.add_foreignid_attribute('subject_id')
    schema.add_foreignid_attribute('data_batch_id')
    schema.add_foreignid_attribute('wix_run_id')
    schema.add_categoric_attribute('string_value')
    return schema

