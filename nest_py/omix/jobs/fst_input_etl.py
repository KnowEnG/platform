
import nest_py.core.jobs.file_utils as file_utils
import os
import math

def _make_fst_config(comparison_key, data_dir, otu_defs):
    num_features = len(otu_defs)
    config = dict()
    config['results_directory'] = fst_results_dirname(comparison_key, data_dir)
    config['data_path'] = filename_of_fst_input_csv(comparison_key, data_dir)
    config['feature_metadata_path'] = filename_of_fst_metadata(data_dir)
    config['data_label'] = comparison_key
    config['response'] = 'cohort'
    config['to_drop'] = ['cohort']
    config['mode'] = 'classification'
    config['vim_score'] = 'MeanDecreaseAccuracy'
    config['ntree'] = 10000
    config['mtry'] = int(math.sqrt(float(num_features)))
    config['refuse_subsets'] = 0
    config['refuse_forests'] = 10
    config['refuse_search_parameters'] = False
    config['refuse_compare_methods'] = False
    config['refuse_node_size'] = 1
    return config

def _make_debugging_config(comparison_key, data_dir, otu_defs):
    """
    runs complete analysis, but fast and less accurate
    """
    num_features = len(otu_defs)
    config = _make_fst_config(comparison_key, data_dir, otu_defs)
    config['ntree'] = 100
    config['mtry'] = 10
    config['refuse_subsets'] = 0
    config['refuse_forests'] = 3
    config['refuse_search_parameters'] = False
    config['refuse_compare_methods'] = False
    config['refuse_node_size'] = 5
    return config

def dump_comparison_classification(comparison_key, cohortA_tle, cohortB_tle, 
    geno_samples, otu_defs, data_dir, file_owner=None):
    """
    comparison_key(string)
    geno_sample (list of geno_sample tle)
    otus (list of otu_def tle)
    """
    fn = filename_of_fst_input_csv(comparison_key, data_dir)
    if not os.path.exists(fn):
        row_data = _compile_fst_input_blobs(cohortA_tle, cohortB_tle, geno_samples, otu_defs)
        column_names = _classification_column_names(otu_defs)
        file_utils.dump_csv(fn, column_names, row_data, file_owner=file_owner)
    return

def dump_feature_metadata(otu_defs, data_dir, file_owner=None):
    column_names = ['feature', 'group']
    feature_names = _classification_column_names(otu_defs)
    metadata_rows = list()
    for feature_name in feature_names:
        row = dict()
        row['feature'] = feature_name
        row['group'] = 'OTU'
        metadata_rows.append(row)
    fn = filename_of_fst_metadata(data_dir)
    file_utils.dump_csv(fn, column_names, metadata_rows, file_owner=file_owner)
    return

def filename_of_fst_input_csv(comparison_key, data_dir):
    """
    the filename for the csv file that will be the input to FST analysis
    """
    fst_dir = fst_comp_workspace_dirname(comparison_key, data_dir)
    fn = fst_dir + comparison_key + '-cohort_vs_otus.csv' 
    return fn

def filename_of_fst_metadata(data_dir):
    common_dir =  fst_workspace_dirname(data_dir)
    fn = common_dir + 'common_feature_metadata.csv'
    return fn

def fst_results_dirname(comparison_key, data_dir):
    dn = fst_comp_workspace_dirname(comparison_key, data_dir) + 'results/'
    return dn

def fst_comp_workspace_dirname(comparison_key, data_dir):
    """
    data_dir(string): job's toplevel data directory
    """
    dirname = fst_workspace_dirname(data_dir) + comparison_key + '/'
    return dirname

def fst_workspace_dirname(data_dir):
    fst_workspace = data_dir + '/fst_workspace/'
    return fst_workspace

def _classification_column_names(otu_defs):
    """
    column names for a csv file being used for a classification problem
    between two cohorts.
    First column is 'cohort' (predicted variable).
    Remaining columns are otu names (input features)
    """
    column_names = list()
    column_names.append('cohort')
    for otu_def in otu_defs:
        otu_name = otu_def.get_value('tornado_observation_key')
        column_names.append(otu_name)
    return column_names


def _compile_fst_input_blobs(cohortA_tle, cohortB_tle, geno_samples, otu_defs):
    """
    list of dicts that map 1:1 with rows in the csv file that will be the
    input to the FST computation.
    """
    samples_by_nest_id= dict()
    for sample_key in geno_samples:
        smpl = geno_samples[sample_key]
        nest_id = smpl.get_nest_id()
        samples_by_nest_id[nest_id] = smpl
        row_data = list()

    #print('samples_by_nest_id: ' + str(samples_by_nest_id))
    
    for cohort in [cohortA_tle, cohortB_tle]:
        cohort_name = cohort.get_value('display_name_short')
        sample_ids = cohort.get_value('sample_ids')
        for sample_id in sample_ids:
            row = dict()
            row['cohort'] = cohort_name
            #print('looking for sample: ' + str(sample_id))
            geno_sample = samples_by_nest_id[sample_id]
            sample_otu_abundances = geno_sample.get_value('otu_frac_abundances')
            for otu_def in otu_defs:
                otu_tornado_idx = otu_def.get_value('index_within_tornado_run')
                otu_name = otu_def.get_value('tornado_observation_key')
                otu_val = sample_otu_abundances.get_value(otu_tornado_idx)
                row[otu_name] = otu_val
            row_data.append(row)
    return row_data 

