"""
Associations between entries in the jobs table and entries in the
ssviz_spreadsheets table.
"""

from nest_py.core.data_types.tablelike_schema import TablelikeSchema

COLLECTION_NAME = 'ssviz_jobs_spreadsheets'

def generate_schema():
    schema = TablelikeSchema(COLLECTION_NAME)
    schema.add_foreignid_attribute('job_id')
    schema.add_foreignid_attribute('ssviz_spreadsheet_id')

    schema.add_index(['job_id'])
    return schema
