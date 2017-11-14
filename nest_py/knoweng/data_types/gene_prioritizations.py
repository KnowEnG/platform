
from nest_py.core.data_types.tablelike_schema import TablelikeSchema

COLLECTION_NAME = 'gene_prioritizations'

def generate_schema():
    schema = TablelikeSchema(COLLECTION_NAME)
    schema.add_foreignid_attribute('job_id')
    schema.add_json_attribute('scores')
    schema.add_numeric_attribute('minimum_score')
    schema.add_json_attribute('gene_ids_to_names')
    return schema

