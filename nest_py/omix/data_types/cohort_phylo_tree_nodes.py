"""
The attributes of the nodes of a phylogenetic tree (taxonomy) for a single
cohort. This is the primary place analytics results for a cohort's
taxonomy are kept.
"""

from nest_py.core.data_types.tablelike_schema import TablelikeSchema

#FIXME this needs to go somewhere more generic
NUM_QUANTILES = 20

COLLECTION_NAME = 'cohort_phylo_tree_nodes'

def generate_schema():
    num_quantile_levels = NUM_QUANTILES + 1

    schema = TablelikeSchema(COLLECTION_NAME)

    schema.add_foreignid_attribute('cohort_id')

    schema.add_categoric_attribute('node_level', valid_values=None)
    schema.add_categoric_attribute('node_name', valid_values=None)
    schema.add_numeric_attribute('node_idx', min_val=0)
    schema.add_numeric_attribute('parent_node_idx', min_val=-1)

    schema.add_index(['cohort_id', 'node_level'])
    schema.add_index(['cohort_id', 'parent_node_idx'])

    #schema.add_numeric_attribute('num_unique_otus_median', 
    #    min_val=0, max_val=None)
    schema.add_numeric_attribute('num_unique_otus_mean', 
        min_val=0, max_val=None)
    #schema.add_numeric_list_attribute('num_unique_otus_quantiles', 
    #    min_val=None, max_val=None, 
    #    min_num_vals=num_quantile_levels, max_num_vals=num_quantile_levels)
    schema.add_numeric_list_attribute('num_unique_otus_density_plot_x', 
        min_val=0.0, max_val=None, 
        min_num_vals=None, max_num_vals=None)
    schema.add_numeric_list_attribute('num_unique_otus_density_plot_y',
         min_val=0.0, max_val=None, 
         min_num_vals=None, max_num_vals=None)

    schema.add_numeric_list_attribute('num_unique_otus_histo_bin_start_x', 
        min_val=0.0, max_val=None, 
        min_num_vals=None, max_num_vals=None)
    schema.add_numeric_list_attribute('num_unique_otus_histo_bin_end_x', 
        min_val=0.0, max_val=None, 
        min_num_vals=None, max_num_vals=None)
    schema.add_numeric_list_attribute('num_unique_otus_histo_bin_height_y', 
        min_val=0.0, max_val=None, 
        min_num_vals=None, max_num_vals=None)
    schema.add_numeric_attribute('num_unique_otus_histo_num_zeros', 
        min_val=0.0, max_val=None) 

    schema.add_numeric_attribute('normalized_entropy_mean',
        min_val=0, max_val=None)
    schema.add_numeric_list_attribute('normalized_entropy_histo_bin_start_x',
        min_val=0.0, max_val=None,
        min_num_vals=None, max_num_vals=None)
    schema.add_numeric_list_attribute('normalized_entropy_histo_bin_end_x',
        min_val=0.0, max_val=None,
        min_num_vals=None, max_num_vals=None)
    schema.add_numeric_list_attribute('normalized_entropy_histo_bin_height_y',
        min_val=0.0, max_val=None,
        min_num_vals=None, max_num_vals=None)
    schema.add_numeric_attribute('normalized_entropy_histo_num_zeros',
        min_val=0.0, max_val=None)

    #schema.add_numeric_attribute('relative_abundance_median', 
    #    min_val=0, max_val=None) 
    schema.add_numeric_attribute('relative_abundance_mean', 
        min_val=0, max_val=None)
    schema.add_numeric_list_attribute('relative_abundance_quantiles', 
        min_val=None, max_val=None, 
        min_num_vals=num_quantile_levels, max_num_vals=num_quantile_levels)
    #schema.add_numeric_list_attribute('relative_abundance_density_plot_x', 
    #    min_val=0.0, max_val=None, 
    #    min_num_vals=num_quantile_levels, max_num_vals=num_quantile_levels)
    #schema.add_numeric_list_attribute('relative_abundance_density_plot_y', 
    #    min_val=0.0, max_val=None, 
    #    min_num_vals=num_quantile_levels, max_num_vals=num_quantile_levels)
 
    schema.add_numeric_list_attribute('relative_abundance_histo_bin_start_x', 
        min_val=0.0, max_val=None, 
        min_num_vals=None, max_num_vals=None)
    schema.add_numeric_list_attribute('relative_abundance_histo_bin_end_x', 
        min_val=0.0, max_val=None, 
        min_num_vals=None, max_num_vals=None)
    schema.add_numeric_list_attribute('relative_abundance_histo_bin_height_y', 
        min_val=0.0, max_val=None, 
        min_num_vals=None, max_num_vals=None)
    schema.add_numeric_attribute('relative_abundance_histo_num_zeros', 
        min_val=0.0, max_val=None) 

    return schema

