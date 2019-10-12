"""
a Cohort Comparison defines a baseline cohort, and then a 
variant cohort and individual patient to compare to it.

The cohorts must all share the same tornado_run_id.
"""

from nest_py.core.data_types.tablelike_schema import TablelikeSchema

COLLECTION_NAME = 'cohort_comparisons'

def generate_schema():
    schema = TablelikeSchema(COLLECTION_NAME)
    schema.add_categoric_attribute('display_name', valid_values=None)
    schema.add_foreignid_attribute('baseline_cohort_id')
    schema.add_foreignid_attribute('variant_cohort_id')
    schema.add_foreignid_attribute('patient_cohort_id')
    schema.add_foreignid_list_attribute('top_fst_ranked_otu_ids', valid_values=None)
    schema.add_numeric_list_attribute('top_fst_ranked_otu_scores')
    return schema

