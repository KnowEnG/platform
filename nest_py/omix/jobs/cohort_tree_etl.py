"""
routines for creating the tree structures to be
uploaded to the api from the outputs of the
cohort_analysis methods

"""

from nest_py.core.jobs.checkpoint import CheckpointTimer
from nest_py.core.jobs.jobs_logger import log
import nest_py.core.data_types.tablelike_entry as tablelike_entry
import nest_py.omix.data_types.cohort_phylo_tree_nodes as cohort_phylo_tree_nodes

def upload_nodes(client_registry, cohort_def, cohort_tree, timer=None):
    """
    takes a cohort definition and a taxonomy tree that has been populated
    with analytics results. uploads the individual nodes with those attributes
    that are part of the api
    """
    if timer is None:
        timer = CheckpointTimer("Cohort_Tree_Upload")
    cohort_name = cohort_def.get_value('display_name_short')
    timer.checkpoint('begin cohort tree upload: ' + cohort_name)
    nodes_client = client_registry[cohort_phylo_tree_nodes.COLLECTION_NAME]
    cohort_id = cohort_def.get_nest_id().get_value()
    node_tles = _extract_cohort_node_tles(cohort_tree, cohort_id)
    num_uploaded = nodes_client.bulk_create_entries_async(node_tles, batch_size=3000)
    assert(not num_uploaded is None)
    timer.checkpoint('tree upload complete for: ' + cohort_name)
    return

def _extract_cohort_node_tles(cohort_tree, cohort_id):
    """
    creates a tablelike_entry of a cohort_phylo_tree_node for
    the top of the input tree, and then appends node tles
    for all child trees. returned list is essentially DFS, with
    attributes of the nodes converted to tles
    """
    nodes_schema = cohort_phylo_tree_nodes.generate_schema()
    node_level = cohort_tree.get_attribute('node_level')
    node_name = cohort_tree.get_attribute('node_name')
    node_idx= cohort_tree.get_attribute('node_idx')
    parent_node_idx = cohort_tree.get_attribute('parent_node_idx')

    relative_abundance_mean = cohort_tree.get_attribute('abundance_frac_mean')
    relative_abundance_quantiles = cohort_tree.get_attribute(
        'abundance_frac_quantiles')
    rel_ab_histo_x_s= cohort_tree.get_attribute('abundance_frac_histo_bin_start_x')
    rel_ab_histo_x_e = cohort_tree.get_attribute('abundance_frac_histo_bin_end_x')
    rel_ab_histo_y = cohort_tree.get_attribute('abundance_frac_histo_bin_height_y')
    rel_ab_zero_count = cohort_tree.get_attribute('abundance_frac_histo_num_zeros')

    num_unique_otus_median = cohort_tree.get_attribute('num_unique_otus_median')
    num_unique_otus_mean = cohort_tree.get_attribute('num_unique_otus_mean')
    num_unique_otus_quantiles = cohort_tree.get_attribute(
        'num_unique_otus_quantiles')
    num_unique_otus_x_coords= cohort_tree.get_attribute(
        'num_unique_otus_density_plot_x')
    num_unique_otus_y_coords= cohort_tree.get_attribute(
        'num_unique_otus_density_plot_y')

    unique_otus_histo_x_s= cohort_tree.get_attribute(
        'num_unique_otus_histo_bin_start_x')
    unique_otus_histo_x_e = cohort_tree.get_attribute(
        'num_unique_otus_histo_bin_end_x')
    unique_otus_histo_y = cohort_tree.get_attribute(
        'num_unique_otus_histo_bin_height_y')
    unique_otus_zero_count = cohort_tree.get_attribute(
        'num_unique_otus_histo_num_zeros')

    norm_ent_mean = cohort_tree.get_attribute('normalized_entropy_mean')
    norm_ent_histo_x_s= cohort_tree.get_attribute(
        'normalized_entropy_histo_bin_start_x')
    norm_ent_histo_x_e = cohort_tree.get_attribute(
        'normalized_entropy_histo_bin_end_x')
    norm_ent_histo_y = cohort_tree.get_attribute(
        'normalized_entropy_histo_bin_height_y')
    norm_ent_zero_count = cohort_tree.get_attribute(
        'normalized_entropy_histo_num_zeros')

    tle = tablelike_entry.TablelikeEntry(nodes_schema)
    tle.set_value('cohort_id', cohort_id)
    tle.set_value('node_level', node_level)
    tle.set_value('node_name', node_name)
    tle.set_value('node_idx', node_idx)
    tle.set_value('parent_node_idx', parent_node_idx)

    tle.set_value('relative_abundance_mean', relative_abundance_mean)
    tle.set_value('relative_abundance_quantiles', relative_abundance_quantiles)
    tle.set_value('relative_abundance_histo_bin_start_x', rel_ab_histo_x_s)
    tle.set_value('relative_abundance_histo_bin_end_x', rel_ab_histo_x_e)
    tle.set_value('relative_abundance_histo_bin_height_y', rel_ab_histo_y)
    tle.set_value('relative_abundance_histo_num_zeros', rel_ab_zero_count)

    tle.set_value('num_unique_otus_mean', num_unique_otus_mean)
    tle.set_value('num_unique_otus_density_plot_x', num_unique_otus_x_coords)
    tle.set_value('num_unique_otus_density_plot_y', num_unique_otus_y_coords)
    tle.set_value('num_unique_otus_histo_bin_start_x', unique_otus_histo_x_s)
    tle.set_value('num_unique_otus_histo_bin_end_x', unique_otus_histo_x_e)
    tle.set_value('num_unique_otus_histo_bin_height_y', unique_otus_histo_y)
    tle.set_value('num_unique_otus_histo_num_zeros', unique_otus_zero_count)

    tle.set_value('normalized_entropy_mean', norm_ent_mean)
    tle.set_value('normalized_entropy_histo_bin_start_x', norm_ent_histo_x_s)
    tle.set_value('normalized_entropy_histo_bin_end_x', norm_ent_histo_x_e)
    tle.set_value('normalized_entropy_histo_bin_height_y', norm_ent_histo_y)
    tle.set_value('normalized_entropy_histo_num_zeros', norm_ent_zero_count)

    tle_lst = list()
    tle_lst.append(tle)
    for child_tree in cohort_tree.get_children():
        child_tles = _extract_cohort_node_tles(child_tree, cohort_id)
        tle_lst += child_tles
    return tle_lst

