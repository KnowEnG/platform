
from operator import itemgetter

import nest_py.core.jobs.file_utils as file_utils
import nest_py.omix.jobs.fst_input_etl as fst_input_etl

def load_fst_results_from_csv(comparison_key, data_dir):
    fn = filename_of_fst_results(comparison_key, data_dir)
    #corresponds to the tornado_observation_key, which is just a number x for OTU-x
    key_col = 'index'
    results_by_otu_num = file_utils.csv_file_to_nested_dict(fn, key_col)
    return results_by_otu_num

def post_process_fst_results(comparison_key, results_by_otu_num, otu_defs):
    """
    adds ranks and otu ids to results entries
    returns a list of dicts sorted by the rank
        {
            display_score: flt
            otu_tle: otu_def tablelike
            ranking: int
            tornado_observation_key: string
        }
    """
    if comparison_key in ['wenbin_fecal_aoah', 'wenbin_cecum_aoah', 'wenbin_all_aoah']:
        #I don't want this to happen without it being expected, as it's a
        #serious sign something is wrong if not
        print("Giving otus with no scores MAX_SCORE")
        for otu_def in otu_defs:
            tornado_obs_key = otu_def.get_value('tornado_observation_key')
            if not tornado_obs_key in results_by_otu_num:
                result = dict()
                result['index'] = tornado_obs_key
                result['VIM_mean'] = -1.0
                result['p_value'] = -1
                result['VIM_var'] =  1.0
                results_by_otu_num[tornado_obs_key] = result
    #add the otu_tle to the result
    for otu_def in otu_defs:
        tornado_obs_key = otu_def.get_value('tornado_observation_key')
        result_blob = results_by_otu_num[tornado_obs_key]
        assert('otu_tle' not in result_blob)
        result_blob['otu_tle'] = otu_def
        result_blob['tornado_observation_key'] = tornado_obs_key

    #add a cleaned up score
    result_blobs = results_by_otu_num.values()
    for result_blob in result_blobs:
        vim_score = float(result_blob['VIM_mean'])
        if vim_score > 0.0:
            clean_score = vim_score
        else:
            clean_score = 0.0
        result_blob['display_score'] = clean_score

    #add a rank
    sorted_result_blobs = sorted(result_blobs, key=itemgetter('display_score'))
    sorted_result_blobs.reverse()
    next_rank = 0
    for result_blob in sorted_result_blobs:
        result_blob['ranking'] = next_rank
        next_rank += 1
    assert(next_rank == len(sorted_result_blobs))

    return sorted_result_blobs

def filename_of_fst_results(comparison_key, data_dir):
    basename = 'REFUSE_Table.csv'
    fst_dir = fst_input_etl.fst_results_dirname(comparison_key, data_dir)
    abs_filename = fst_dir + 'output_refuse/' + basename
    return abs_filename

 
