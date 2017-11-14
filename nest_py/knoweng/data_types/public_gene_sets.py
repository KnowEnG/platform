"""
A collection of public gene sets.
"""

from nest_py.core.data_types.tablelike_schema import TablelikeSchema

COLLECTION_NAME = 'public_gene_sets'

def generate_schema():
    schema = TablelikeSchema(COLLECTION_NAME)
    schema.add_categoric_attribute('set_id', valid_values=None)
    schema.add_categoric_attribute('set_name', valid_values=None)
    schema.add_numeric_attribute('species_id')
    schema.add_numeric_attribute('gene_count')
    schema.add_categoric_attribute('collection', valid_values=None)
    schema.add_categoric_attribute('edge_type_name', valid_values=None)
    schema.add_categoric_attribute('supercollection', valid_values=None)
    schema.add_categoric_attribute('url', valid_values=None)

    schema.add_index(['set_id'])
    return schema

