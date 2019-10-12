
from nest_py.core.data_types.tablelike_schema import TablelikeSchema

COLLECTION_NAME = 'gene_set_characterizations'

def generate_schema():
    schema = TablelikeSchema(COLLECTION_NAME)
    schema.add_foreignid_attribute('job_id')
    schema.add_jsonb_attribute('user_gene_sets')
    schema.add_jsonb_attribute('set_level_scores')
    schema.add_numeric_attribute('minimum_score')
    return schema
