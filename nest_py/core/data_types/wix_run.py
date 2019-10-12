"""
Data type with some basic info on a 'run', including it's config 
and whether it's done. Mostly used for its 'id' field to attach
to data generated during the run.
"""

from nest_py.core.data_types.tablelike_schema import TablelikeSchema
from nest_py.core.data_types.tablelike_entry import TablelikeEntry

COLLECTION_NAME = 'wix_run'

def generate_schema():
    """
    """
    schema = TablelikeSchema(COLLECTION_NAME)
    schema.add_categoric_attribute('job_name')
    schema.add_categoric_attribute('local_results_name')
    schema.add_categoric_attribute('status')
    schema.add_categoric_attribute('start_time')
    schema.add_categoric_attribute('end_time')
    schema.add_json_attribute('config')
    return schema

