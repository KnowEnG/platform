from nest_py.core.data_types.tablelike_schema import TablelikeSchema

COLLECTION_NAME = 'signature_analyses'

def generate_schema():
    schema = TablelikeSchema(COLLECTION_NAME)
    schema.add_foreignid_attribute('job_id')
    schema.add_jsonb_attribute('scores')
    return schema
