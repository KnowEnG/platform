"""
routines for constructing known cohorts by filtering raw Mayo_March16 data
and also uploading cohort definitions (but not analytics) to the api

tightly coupled to mmbdb_seed_job
"""

import nest_py.omix.data_types.cohorts as cohorts
from nest_py.core.data_types.tablelike_entry import TablelikeEntry

def upload_cohort(client_registry, cohort_config, 
    cohort_sample_ids, tornado_run_id):
    """
    cohort_config is a dict with string values for
        display_name_short, display_name_long, and query.

    """
    cohorts_schema = cohorts.generate_schema()
    cohorts_client = client_registry[cohorts.COLLECTION_NAME]
    
    cohort_tle = TablelikeEntry(cohorts_schema)
    cohort_tle.set_value('display_name_short', cohort_config['display_name_short'])
    cohort_tle.set_value('display_name_long',  cohort_config['display_name_long'])
    cohort_tle.set_value('tornado_run_id' , tornado_run_id)
    cohort_tle.set_value('query', cohort_config['query'])
    cohort_tle.set_value('sample_ids', cohort_sample_ids)
    cohort_tle.set_value('num_samples', len(cohort_sample_ids))

    cohort_tle = cohorts_client.create_entry(cohort_tle)
    assert(not cohort_tle is None)
    return cohort_tle

def filter_tornado_keys_biom_kvp(biom_table, query_key, query_val):
    """
    Does a simple filter on the samples metadata from the *biom_table* to get
    a list of sample_tornado_ids that match the filter. 

    The filter acceptance criteria is query_key=query_val. Only one query
    param is supported, and must be stored as sample metadata in the
    biom_table

    returns a list of strings of nest_ids of the geno_samples that matched the
    filter 
    """
    matching_tornado_keys = list()
    tornado_sample_keys = biom_table.ids('sample')
    for tornado_sample_key in tornado_sample_keys:
        bt_sample_metadata = biom_table.metadata(tornado_sample_key, 'sample')
        obs_val = bt_sample_metadata[query_key]
        if obs_val == query_val:
            matching_tornado_keys.append(tornado_sample_key)

    print('num samples found by cohort filter:' + 
        str(len(matching_tornado_keys)))

    return matching_tornado_keys

def filter_tornado_keys_patient_data_kvp(all_patient_data, 
    study_key, query_key, query_val):
    """
    Does a simple kvp filter against the patient data from a study  using the
    data structure loaded by patient_data_etl.load_all_metadata.

    returns a list of tornado_sample_keys
    """

    cohort_sample_keys = list()
    study_data = all_patient_data[study_key]
    for tornado_sample_key in study_data['patients']:
        patient_data = study_data['patients'][tornado_sample_key]
        if patient_data[query_key] == query_val:
            cohort_sample_keys.append(tornado_sample_key)
    return cohort_sample_keys

def tornado_sample_keys_to_nest_ids(tornado_sample_keys, all_geno_samples):
    """
    returns a list of strings of nest_ids of the geno_samples that have
    a tornado_sample_key in the input list
    """
    nest_ids = list()
    at_least_one_found = False
    num_found = 0
    for tornado_sample_key in tornado_sample_keys:
        #the key might not be in the samples if subsampling, so don't
        #crash, just move on. The patient metadata doesn't know to 
        #subsample until right here
        if tornado_sample_key in all_geno_samples:
            num_found += 1
            at_least_one_found = True
            geno_sample = all_geno_samples[tornado_sample_key]
            nest_id = geno_sample.get_nest_id()
            nest_ids.append(nest_id)
    if not at_least_one_found:
        raise Exception("No nest_ids were found for a cohort's geno samples.  Either subsampling is too aggressive and zero samples of the cohort had their genome data loaded, or there is a key matching problem. Either way, cohort construction can't be completed.")
    if not num_found == len(tornado_sample_keys):
        print('found ' + str(num_found) + ' / ' + str(len(tornado_sample_keys)) + ' samples by tornado_sample_key.')
    return nest_ids 

