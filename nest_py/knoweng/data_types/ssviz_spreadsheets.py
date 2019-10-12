"""
Information about individual spreadsheets as they're used in the spreadsheet
visualizer.
"""

from nest_py.core.data_types.tablelike_schema import TablelikeSchema

COLLECTION_NAME = 'ssviz_spreadsheets'

def generate_schema():
    schema = TablelikeSchema(COLLECTION_NAME)
    schema.add_foreignid_attribute('file_id')
    schema.add_boolean_attribute('is_file_samples_as_rows')
    # the sample names from the spreadsheet, ordered as they appear in the file
    schema.add_categoric_list_attribute('sample_names', valid_values=None)
    # the feature names from the spreadsheet, ordered as they appear in the file
    schema.add_categoric_list_attribute('feature_names', valid_values=None)
    # the feature types from the spreadsheet, ordered as they appear in the file
    schema.add_categoric_list_attribute('feature_types', \
        valid_values=['numeric', 'categoric', 'other'])
    schema.add_int_list_attribute('feature_nan_counts')
    schema.add_int_list_attribute('sample_nan_counts')
    schema.add_index(['file_id'])
    return schema
