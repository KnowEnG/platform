from nest_py.omix.jobs.sparse_array import SparseArray
from nest_py.omix.jobs.attribute_tree import AttributeTree
import nest_py.omix.jobs.cohort_analysis as cohort_analysis
import nest_py.omix.jobs.otu_analysis as otu_analysis

def test_quantiles_of_sparse_ary():
    ary_size = 12
    sary = SparseArray(ary_size, not_set_value=0.0)
    sary.set_value(0, 1.0)
    sary.set_value(1, 2.0)
    sary.set_value(2, 2.0)
    sary.set_value(3, 3.0)
    sary.set_value(7, 4.0)
    sary.set_value(8, 5.0)
    obs_quants = cohort_analysis._quantiles_of_sparse_ary(sary, 4)
    #note: we are using 'linear' interpolation from numpy lib. that's
    #why these values aren't values between elements of sary
    exp_quants = [0.0, 0.0, 0.5, 2.25, 5.0]
    assert exp_quants == obs_quants
    return

def test_pdf_scatterplots_of_quantiles():
    #overlapping quantiles at the beginning
    quantiles = [0.0, 0.0, 4.0, 8.0, 12.0]
    exp_x_coords = [0.0, 2.0, 6.0, 10.0, 12.0]
    exp_y_coords = [0.0, 0.125, 0.063, 0.063, 0.0]
    obs_x_coords, obs_y_coords = cohort_analysis._pdf_scatterplots_of_quantiles(
        quantiles)
    assert exp_x_coords == obs_x_coords
    assert exp_y_coords == obs_y_coords
    
    #overlapping quantiles at the middle and end
    quantiles = [0.0, 2.0, 2.0, 12.0, 12.0]
    exp_x_coords = [0.0, 1.0, 7.0, 12.0]
    exp_y_coords = [0.0, 0.125, 0.075, 0.0]
    obs_x_coords, obs_y_coords = cohort_analysis._pdf_scatterplots_of_quantiles(
        quantiles)
    assert exp_x_coords == obs_x_coords
    assert exp_y_coords == obs_y_coords
    
def test_set_node_idxs():
    """
    check the numbering that gets assigned to the taxonomy tree
    (and the parent node reference idx)
    """
    root = AttributeTree()
    root.set_attribute('exp_node_idx', 0)
    root.set_attribute('exp_parent_node_idx', -1)

    node_1a = AttributeTree()
    node_1a.set_attribute('exp_node_idx', 1)
    node_1a.set_attribute('exp_parent_node_idx', 0)
    root.add_child(node_1a)
    
    node_1a2a = AttributeTree()
    node_1a2a.set_attribute('exp_node_idx', 2)
    node_1a2a.set_attribute('exp_parent_node_idx', 1)
    node_1a.add_child(node_1a2a)

    node_1a2b = AttributeTree()
    node_1a2b.set_attribute('exp_node_idx', 3)
    node_1a2b.set_attribute('exp_parent_node_idx', 1)
    node_1a.add_child(node_1a2b)

    node_1b = AttributeTree()
    node_1b.set_attribute('exp_node_idx', 4)
    node_1b.set_attribute('exp_parent_node_idx', 0)
    root.add_child(node_1b)

    node_1b2c = AttributeTree()
    node_1b2c.set_attribute('exp_node_idx', 5)
    node_1b2c.set_attribute('exp_parent_node_idx', 4)
    node_1b.add_child(node_1b2c)

    otu_analysis._set_node_idxs(root)
    _assert_node_idx_agreement(root)
    return

def _assert_node_idx_agreement(test_tree):
    """
    recursive loop to check the exp/obs node_idxs at
    each node
    """
    obs_node_idx = test_tree.get_attribute('node_idx')
    exp_node_idx = test_tree.get_attribute('exp_node_idx')
    assert(obs_node_idx == exp_node_idx)

    obs_parent_idx = test_tree.get_attribute('parent_node_idx')
    exp_parent_idx = test_tree.get_attribute('exp_parent_node_idx')
    assert(obs_parent_idx == exp_parent_idx)

    for child in test_tree.get_children():
        _assert_node_idx_agreement(child)
    return



