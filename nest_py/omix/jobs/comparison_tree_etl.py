"""
routines for creating the final data structures to upload to
the api from the outputs of comparison_analysis. Also does
the uploading to the api.
"""
from nest_py.core.jobs.jobs_logger import log
import nest_py.core.data_types.tablelike_entry as tablelike_entry
import nest_py.omix.data_types.comparison_phylo_tree_nodes as comparison_phylo_tree_nodes

def upload_nodes(client_registry, comparison_def, comparison_tree):
    """
    """
    nodes_client = client_registry[comparison_phylo_tree_nodes.COLLECTION_NAME]

    comparison_id = comparison_def.get_nest_id()

    node_tles = _extract_comparison_node_tles(comparison_tree, comparison_id)
    node_tles = nodes_client.bulk_create_entries_async(node_tles, batch_size=6000)
    assert(not node_tles is None)
    return

def _extract_comparison_node_tles(comparison_tree, comparison_id):
    nodes_schema = comparison_phylo_tree_nodes.generate_schema()

    node_level = comparison_tree.get_attribute('node_level')
    node_name = comparison_tree.get_attribute('node_name')
    node_idx = comparison_tree.get_attribute('node_idx')
    parent_node_idx = comparison_tree.get_attribute('parent_node_idx')
    ranks_in_node = comparison_tree.get_attribute('ranks_in_node')
    
    tle = tablelike_entry.TablelikeEntry(nodes_schema)
    tle.set_value('comparison_id', comparison_id)
    tle.set_value('node_level', node_level)
    tle.set_value('node_name', node_name)
    tle.set_value('node_idx', node_idx)
    tle.set_value('parent_node_idx', parent_node_idx)
    tle.set_value('top_fst_otu_rankings_in_node', ranks_in_node)

    tle_lst = list()
    tle_lst.append(tle)
    for child_tree in comparison_tree.get_children():
        child_tles = _extract_comparison_node_tles(child_tree, comparison_id)
        tle_lst += child_tles
    return tle_lst


