
from nest_py.omix.jobs.attribute_tree import AttributeTree
import nest_py.omix.data_types.otus as otus

def compute_taxonomy_tree(otu_defs): 
    """
    note that in this taxonomy tree, OTUs are a level *below* species, as
    multiple OTUs can map to the same species
    """
    tree_root = AttributeTree()
    taxa_levels = otus.TAXONOMY_LEVELS
    tree_root.set_attribute('node_level', 'root')
    tree_root.set_attribute('node_name', 'root')
    for otu_def in otu_defs:
        current_node = tree_root
        for taxa_level in taxa_levels:
            taxa_name = otu_def.get_value(taxa_level)
            existing_child = current_node.find_child('node_name',taxa_name)
            if existing_child is None:
                new_node = AttributeTree()
                new_node.set_attribute('node_level', taxa_level)
                new_node.set_attribute('node_name', taxa_name)
                current_node.add_child(new_node)
                current_node = new_node
            else: 
                current_node = existing_child
                current_level = current_node.get_attribute('node_level')
                assert(current_level == taxa_level)
        #add the otu as if it is a level below species
        species_node = current_node
        otu_name = otu_def.get_value('otu_name')
        existing_otu_node = species_node.find_child('node_name', otu_name)
        if existing_otu_node is None:
            otu_idx = otu_def.get_value('index_within_tornado_run')
            otu_node = AttributeTree()
            otu_node.set_attribute('node_level', 'otu_name')
            otu_node.set_attribute('node_name', otu_name)
            otu_node.set_attribute('otu_index', otu_idx)
            species_node.add_child(otu_node)
    _set_node_idxs(tree_root)
    #logger.pretty_print_jdata(tree_root.to_jdata())
    return tree_root

def _set_node_idxs(tree_root):
    _set_node_idxs_rec(tree_root, 0)
    _set_parent_node_idxs(tree_root)
    return

def _set_node_idxs_rec(taxonomy_tree, idx_offset):
    taxonomy_tree.set_attribute('node_idx', idx_offset)
    num_nodes_in_tree = 1
    idx_offset = idx_offset + 1
    for child_tree in taxonomy_tree.get_children():
        num_nodes_in_child = _set_node_idxs_rec(child_tree, idx_offset)
        idx_offset += num_nodes_in_child
        num_nodes_in_tree += num_nodes_in_child
    return num_nodes_in_tree
        
def _set_parent_node_idxs(taxonomy_tree):
    """
    must be called after _set_node_idxs_rec
    """
    node_idx = taxonomy_tree.get_attribute('node_idx')
    if node_idx == 0:
        taxonomy_tree.set_attribute('parent_node_idx', -1)
    for child_tree in taxonomy_tree.get_children():
        child_tree.set_attribute('parent_node_idx', node_idx)
        _set_parent_node_idxs(child_tree)
    return


