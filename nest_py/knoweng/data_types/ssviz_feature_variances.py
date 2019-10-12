"""
Row-level variances for any purely numeric spreadsheets used in the spreadsheet
visualizer.
"""

from nest_py.core.data_types.tablelike_schema import TablelikeSchema

COLLECTION_NAME = 'ssviz_feature_variances'

def generate_schema():
    schema = TablelikeSchema(COLLECTION_NAME)
    schema.add_foreignid_attribute('ssviz_spreadsheet_id')
    # the variances, ordered by row index
    # note this field can contain NaNs
    # if serializing to json, use something like...
    # [None if np.isnan(val) else val for val in scores]
    schema.add_numeric_list_attribute('scores', precision=24, scale=6)
    schema.add_index(['ssviz_spreadsheet_id'])
    return schema
