"""
downloading the files on box that represent manual runs of the feature selection tool.
fst was run on some of the comparisons to rank the OTUs in order of how well they
can separate the baseline cohort from the variant
"""

import csv
import os
import random
import nest_py.ops.container_users as container_users
import nest_py.core.jobs.box_downloads as box_downloads
import nest_py.omix.jobs.fst_input_etl as fst_input_etl
import nest_py.omix.jobs.fst_output_etl as fst_output_etl
import nest_py.core.jobs.file_utils as file_utils

import nest_py.ops.compile_ops as compile_ops
compile_ops.load_libsrc()
from fst import FST

DEBUGGING_CONFIG = False

def get_fst_of_comparison(comparison_key, seed_data,
    cohort_a, cohort_b, otu_defs, geno_samples, data_dir, file_owner):

    fst_cache_url = seed_data.get_fst_results_cache_url(comparison_key)
    if fst_cache_url is None:
        _compute_fst_results_for_comparison(
            comparison_key, cohort_a, cohort_b, 
            otu_defs, geno_samples, data_dir, file_owner)
    else:
        print('Downloading precomputed FST results at: ' + fst_cache_url)
        _download_fst_results_for_comparison(
            comparison_key, fst_cache_url, data_dir, file_owner)

    #the above will have left behind files owned by root
    fst_workspace = fst_input_etl.fst_workspace_dirname(data_dir)
    file_utils.set_directory_owner(file_owner, fst_workspace, recurse=True)

    results = fst_output_etl.load_fst_results_from_csv(comparison_key, data_dir)
    sorted_otu_blobs = fst_output_etl.post_process_fst_results(
        comparison_key, results, otu_defs)
    return sorted_otu_blobs

def _compute_fst_results_for_comparison(comparison_key, cohort_a, cohort_b,
        otu_defs, geno_samples, data_dir, file_owner):

    noprompt=True
    fst_input_etl.dump_comparison_classification(comparison_key, 
        cohort_a, cohort_b, geno_samples, otu_defs, data_dir, 
        file_owner=file_owner)
    fst_input_etl.dump_feature_metadata(otu_defs, data_dir, file_owner=file_owner)

    if DEBUGGING_CONFIG:
        fst_config = fst_input_etl._make_debugging_config(comparison_key, data_dir, otu_defs)
    else:
        fst_config = fst_input_etl._make_fst_config(comparison_key, data_dir, otu_defs)

    scratch_dirname = dirname_of_fst_scratch(data_dir)
    file_utils.ensure_directory(scratch_dirname, file_owner=file_owner)
    os.environ['JOBLIB_TEMP_FOLDER'] = scratch_dirname

    fst_runner = FST(fst_config, noprompt)
    print('begin FST.refuse(): ' + comparison_key)
    fst_runner.refuse()
    print('end FST.refuse(): ' + comparison_key)
    return 

def dirname_of_fst_scratch(data_dir):
    workspace = fst_input_etl.fst_workspace_dirname(data_dir)
    scratch_dirname = workspace + '/tmp/'
    return scratch_dirname

def _download_fst_results_for_comparison(comparison_key, fst_cache_url, 
    data_dir, file_owner):
    """
    fst_cache_url is typically a public box url pointing at FST results

    downloads the csv of fst results from box for the comparison. will
    not download if the file is already on the local machine.

    returns the filename of the file that was downloaded.
    """
    box_url = fst_cache_url
    fn = fst_output_etl.filename_of_fst_results(comparison_key, data_dir)
    box_downloads.download_from_box_no_auth(box_url, fn, 
        file_owner=file_owner, force=True)
    return 

