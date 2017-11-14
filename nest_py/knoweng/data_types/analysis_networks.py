"""
species' super collections and their collections from knowledge network 
"""

from nest_py.core.data_types.tablelike_schema import TablelikeSchema

COLLECTION_NAME = 'analysis_networks'

def generate_schema():
    schema = TablelikeSchema(COLLECTION_NAME)
    schema.add_categoric_attribute('species_number', valid_values=None)
    schema.add_categoric_attribute('analysis_network_name', valid_values=None)
    schema.add_categoric_attribute('edge_type_name', valid_values=None)
    schema.add_boolean_attribute('selected_by_default')
    return schema

