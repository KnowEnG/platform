"""
Row-level correlations for spreadsheets used in the spreadsheet visualizer.
"""

from nest_py.core.data_types.tablelike_schema import TablelikeSchema

COLLECTION_NAME = 'ssviz_feature_correlations'

def generate_schema():
    schema = TablelikeSchema(COLLECTION_NAME)
    # the spreadsheet whose correlation values are stored in this record
    schema.add_foreignid_attribute('ssviz_spreadsheet_id')
    # next two columns identify the spreadsheet row that defines the grouping
    # NOTE: needed to shorten these names so auto-generated index name is
    # short enough for psql
    schema.add_foreignid_attribute('g_spreadsheet_id')
    schema.add_int_attribute('g_feature_idx')
    # the scores, ordered by row index
    # note this field can contain NaNs
    # if serializing to json, use something like...
    # [None if np.isnan(val) else val for val in scores]
    # we cap pval scores (-10log10(pval)) at 200, and precision might as well
    # be a multiple of 4, because the storage cost is 2 bytes per four decimal
    # digits
    schema.add_numeric_list_attribute('scores', precision=24, scale=23)

    schema.add_index(\
        ['ssviz_spreadsheet_id', 'g_spreadsheet_id', 'g_feature_idx'])
    return schema
