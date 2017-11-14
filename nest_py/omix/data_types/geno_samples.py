"""
A single sample and it's measured otu values from a single
tornado run. A sample is identified by the study it comes from
and the key from within the study (or possibly tornado run, we
don't control the namespace). but internally, the eve id of
a geno_sample is how we identify a sample.

"""

from nest_py.core.data_types.tablelike_schema import TablelikeSchema

COLLECTION_NAME = 'geno_samples'

def generate_schema():
    schema = TablelikeSchema(COLLECTION_NAME)
    schema.add_categoric_attribute('study_key', valid_values=None)
    schema.add_foreignid_attribute('tornado_run_id')
    schema.add_categoric_attribute('tornado_sample_key', valid_values=None)
    schema.add_categoric_attribute('study_sample_key', valid_values=None)

    #the ordering of these values is the same as index_within_tornado_run in the otus endpoint
    #FIXME this probably needs to be a new kind of attribute: sparse_numeric_list_attribute
    #schema.add_numeric_list_attribute('otu_counts', min_val=None, max_val=None, min_num_vals=0, max_num_vals=None)
    return schema

