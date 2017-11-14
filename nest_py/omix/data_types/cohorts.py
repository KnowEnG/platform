"""
Cohort datatype that has it's own tablelike endpoint. Cohorts are
not in Tablelike "Batches", however, they are defined and saved one 
at a time.

A Cohort contains some descriptive information about how and when the
cohort was defined, and a list of id's into the 'samples' endpoint that
are in the cohort.
"""

from nest_py.core.data_types.tablelike_schema import TablelikeSchema

COLLECTION_NAME = 'cohorts'

def generate_schema():
    schema = TablelikeSchema(COLLECTION_NAME)
    schema.add_categoric_attribute('display_name_short', valid_values=None)
    schema.add_categoric_attribute('display_name_long', valid_values=None)
    schema.add_foreignid_attribute('tornado_run_id')
    schema.add_categoric_attribute('query', valid_values=None)
    schema.add_numeric_attribute('num_samples', min_val=0, max_val=None)
    schema.add_categoric_list_attribute('sample_ids', valid_values=None,
        min_num_vals=0, max_num_vals=None)
    return schema

