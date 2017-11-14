
from nest_py.core.data_types.tablelike_schema import TablelikeSchema

COLLECTION_NAME = 'sample_clusterings'

def generate_schema():
    schema = TablelikeSchema(COLLECTION_NAME)
    schema.add_foreignid_attribute('job_id')
    schema.add_json_attribute('top_genes')
    schema.add_json_attribute('samples')
    schema.add_json_attribute('genes_heatmap')
    schema.add_json_attribute('samples_heatmap')
    schema.add_json_attribute('phenotypes')
    return schema

