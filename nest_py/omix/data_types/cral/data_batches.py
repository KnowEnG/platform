"""
Data type for a 'batch of data', usually all the entries that
were loaded from a single spreadsheet.

It would also be appropriate to use a single batch entry for
all the data that comes from a single external source like
an API
"""

from nest_py.core.data_types.tablelike_schema import TablelikeSchema
from nest_py.core.data_types.tablelike_entry import TablelikeEntry

COLLECTION_NAME = 'data_batches'

def generate_schema():
    schema = TablelikeSchema(COLLECTION_NAME)

    schema.add_categoric_attribute('batch_name')

    #if the batch came from a file, this can just be the filename
    schema.add_categoric_attribute('description')

    #the 'id' of the run that loaded the data into
    #feature_realizations. TODO: would this be null
    #if the 'batch' was something like 'direct upload by user'
    schema.add_foreignid_attribute('wix_run_id')

    return schema

