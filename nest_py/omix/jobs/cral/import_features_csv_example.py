"""
wix job to load an example csv file into the CRAL database tables. This example
demonstrates explicitly declaring the subjects, features, and data_batch. 
(It is essentially a smoke test for CRAL data)
"""
import os
from nest_py.core.data_types.tablelike_entry import TablelikeEntry
from nest_py.core.data_types.tablelike_schema import TablelikeSchema
import nest_py.core.jobs.file_utils as file_utils
import nest_py.omix.jobs.omix_jobs_db as omix_jobs_db
import nest_py.omix.data_types.cral.feature_variables as feature_variables
import nest_py.omix.data_types.cral.feature_realizations as feature_realizations
import nest_py.omix.data_types.cral.feature_collections as feature_collections
import nest_py.omix.data_types.cral.subjects as subjects
import nest_py.omix.data_types.cral.data_batches as data_batches

def run(jcx):

    #initialize the job, read config to get data file
    omix_jobs_db.init_db_resources(jcx)
    omix_jobs_db.write_job_start(jcx, 'import_features_csv_example')
    config = jcx.get_config_jdata()
    csv_fn = config['data_csv']
    abs_csv_fn = os.path.join(jcx.get_job_global_data_dir(), csv_fn)

    #we have a hardcoded knowledge of what the metadata attributes for
    #the features in the example data file will be. generate that schema
    #and create a 'feature_collection' for all feature_variables that
    #will have those metadata attributes.
    metadata_schema = _generate_metadata_attributes_schema()
    feature_collection_tle = _write_feature_collection(jcx, metadata_schema)

    #the features themselves are based on the column names in the csv file.
    #write the features as 'feature_variables' to the database and associate
    #the feature_collection with them. 
    column_names = file_utils.csv_file_column_names(abs_csv_fn)
    feature_var_tles = _write_feature_variables(jcx, feature_collection_tle, 
        metadata_schema, column_names)

    #the data batch gives a common identifier to the realizations from the csv
    data_batch_tle = _write_data_batch(jcx)

    #read the csv values into memory
    rows_data = file_utils.csv_file_to_nested_dict(abs_csv_fn, 'subject_id')

    #the subject identifiers are based on the first column 
    #in the csv 'subject_id'
    subject_keys = rows_data.keys()
    subject_tles = _write_subjects(jcx, subject_keys)

    #every realization value will need to be associated with all of the above
    realz_tles = _write_feature_realizations(jcx, rows_data.values(),
        data_batch_tle, feature_var_tles, subject_tles)

    #if we haven't failed, declare success and finish the job off
    jcx.declare_success()
    omix_jobs_db.write_job_end(jcx)
    return

def _write_feature_collection(jcx, metadata_schema):

    schema = feature_collections.generate_schema()
    collection = schema.get_name()
    db_client = jcx.runtime()['db_clients'][collection]
    fc_name = jcx.get_config_jdata()['feature_collection']
    fc_desc = jcx.get_config_jdata()['feature_collection_description']
    run_id = jcx.runtime()['wix_run_tle'].get_nest_id()
    nested_schema_jdata = metadata_schema.to_jdata()

    tle = TablelikeEntry(schema)
    tle.set_value('collection_name', fc_name)
    tle.set_value('description', fc_desc)
    tle.set_value('wix_run_id', run_id)
    tle.set_value('metadata_schema', nested_schema_jdata)

    saved_tle = db_client.create_entry(tle)
    if saved_tle is None:
        jcx.log("Failed writing feature_collection entry to database.")
        jcx.declare_failure()
    else:
        jcx.log('Wrote feature_collection \'' + str(fc_name) + '\' to db.')
    return saved_tle

def _write_feature_variables(jcx, feature_collection_tle, 
    metadata_schema, column_names):
    """
    for the columns that represent 'features' to store in the cral data tables,
    write the feature_variables entries to the db.
    """
    schema = feature_variables.generate_schema()
    collection = schema.get_name()
    db_client = jcx.runtime()['db_clients'][collection]
    run_id = jcx.runtime()['wix_run_tle'].get_nest_id()
    feature_collection_id = feature_collection_tle.get_nest_id()
    tles = list()
    for fn in column_names:
        if fn.startswith('feature') or fn.startswith('outcome'):
            tle = TablelikeEntry(schema)
            tle.set_value('feature_collection_id', feature_collection_id)
            tle.set_value('feature_type', 'numeric')
            tle.set_value('local_name', fn)
            tle.set_value('wix_run_id', run_id)

            #note that the metadata field on a feature_variable_tle is
            #a json blob containing all the attributes of a tle 
            #specific to the metadata attributes this type (based on feature_collection)
            #of feature_variable
            metadata_tle = TablelikeEntry(metadata_schema)
            metadata_tle.set_value('full_name', fn)
            #feature names are like 'feature_x0', so last char
            #is the index, and second to last is either 
            #x or y
            x_or_y = fn[-2]
            xy_number = fn[-1]
            metadata_tle.set_value('x_or_y', x_or_y)
            metadata_tle.set_value('xy_number', fn[-1])
            atts = metadata_schema.object_to_flat_jdata(metadata_tle)
            tle.set_value('metadata_attributes', atts)

            tles.append(tle)

    saved_tles = db_client.bulk_create_entries(tles)
    if saved_tles is None:
        jcx.log("Failed writing feature_variables entries to database.")
        jcx.declare_failure()
    else:
        num_saved = len(saved_tles)
        jcx.log('Wrote ' + str(num_saved) + ' feature_variables to db.')
    return saved_tles

def _write_data_batch(jcx):
    schema = data_batches.generate_schema()
    collection = schema.get_name()
    db_client = jcx.runtime()['db_clients'][collection]
    run_id = jcx.runtime()['wix_run_tle'].get_nest_id()
    batch_name = jcx.get_config_jdata()['data_batch']
    csv_fn = jcx.get_config_jdata()['data_csv']

    tle = TablelikeEntry(schema)
    tle.set_value('batch_name', batch_name)
    tle.set_value('description', csv_fn)
    tle.set_value('wix_run_id', run_id)
    saved_tle = db_client.create_entry(tle)

    if saved_tle is None:
        jcx.log("Failed writing data_batch entry to database.")
        jcx.declare_failure()
    else:
        jcx.log('Wrote data_batch \'' + str(batch_name) + '\' to db.')
    return saved_tle

def _write_subjects(jcx, subject_keys):
    schema = subjects.generate_schema()
    collection = schema.get_name()
    db_client = jcx.runtime()['db_clients'][collection]
    run_id = jcx.runtime()['wix_run_tle'].get_nest_id()
    keyspace = jcx.get_config_jdata()['subject_keyspace']
    tles = list()
    for sk in subject_keys:
        tle = TablelikeEntry(schema)
        tle.set_value('key_space', keyspace)
        tle.set_value('official_key', sk)
        tle.set_value('wix_run_id', run_id)
        tles.append(tle)
    saved_tles = db_client.bulk_create_entries(tles)
    if saved_tles is None:
        jcx.log("Failed writing subject entries to database.")
        jcx.declare_failure()
    else:
        num_saved = len(saved_tles)
        jcx.log('Wrote ' + str(num_saved) + ' subjects to db.')
    return saved_tles

def _write_feature_realizations(jcx, rows_data, data_batch_tle,
    feature_var_tles, subject_tles):

    #need to be able to look up subjects' nest_ids by the value in the csv
    subject_ids = dict()
    for s in subject_tles:
        subject_ids[s.get_value('official_key')] = s.get_nest_id()

    #all of the data in our example csv is numeric
    schema = feature_realizations.generate_schema_numeric()
    run_id = jcx.runtime()['wix_run_tle'].get_nest_id()
    data_batch_id = data_batch_tle.get_nest_id()
    tles = list()
    for row in rows_data:
        subject_key = row['subject_id']
        subject_id = subject_ids[subject_key]
        for fv_tle in feature_var_tles:
            tle = TablelikeEntry(schema)
            fv_id = fv_tle.get_nest_id()
            fv_col_name = fv_tle.get_value('local_name')
            val = float(row[fv_col_name])
            tle.set_value('feature_variable_id', fv_id)
            tle.set_value('subject_id', subject_id)
            tle.set_value('data_batch_id', data_batch_id)
            tle.set_value('wix_run_id', run_id)
            tle.set_value('float_value', val)
            tles.append(tle)

    collection = schema.get_name()
    db_client = jcx.runtime()['db_clients'][collection]
    saved_tles = db_client.bulk_create_entries(tles)
    if saved_tles is None:
        jcx.log("Failed writing feature_realization entries to database.")
        jcx.declare_failure()
    else:
        num_saved = len(saved_tles)
        jcx.log('Wrote ' + str(num_saved) + ' feature_realizations to db.')
    return saved_tles

def _generate_metadata_attributes_schema():
    """
    A schema for the metadata of the columns in the example data set.
    The column names are like 'feature_x0', and from that we can
    parse that it is an 'x' with number '0'.
    """
    schema = TablelikeSchema('example_features_metadata')

    schema.add_categoric_attribute('full_name')
    schema.add_categoric_attribute('x_or_y', valid_values=['x', 'y'])
    schema.add_int_attribute('xy_number', min_val=0)

    #the run that loaded this data into the db
    schema.add_foreignid_attribute('wix_run_id')

    return schema
