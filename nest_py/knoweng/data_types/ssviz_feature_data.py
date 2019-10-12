"""
Row data from spreadsheets used in the spreadsheet visualizer.
"""

from nest_py.core.data_types.tablelike_schema import TablelikeSchema

COLLECTION_NAME = 'ssviz_feature_data'

def generate_schema():
    schema = TablelikeSchema(COLLECTION_NAME)
    schema.add_foreignid_attribute('ssviz_spreadsheet_id')
    schema.add_int_attribute('feature_idx')
    # the values for the row, ordered as they appear in the file
    schema.add_json_attribute('values') # using json bc type can be int, float, or str

    schema.add_index(['ssviz_spreadsheet_id', 'feature_idx'])
    return schema
