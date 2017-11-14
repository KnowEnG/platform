"""
routines for computing analytics for a cohort_comparison
"""

import random
from random import shuffle

def compute_all(comp_def, otu_defs, tree):
    """
    making a 'top_random_otu_ranking' attribute for the tree
    """
    num_otus = len(otu_defs)
    rankings_by_otu_idx = _derive_rankings_by_otu_idx(comp_def, otu_defs)
    #rankings is now our order for top otus. the indexes are index_within_tornado_run,
    #the values are the ranks of that otu
    _aggregate_tree_rankings(tree, rankings_by_otu_idx)
    return

def _aggregate_tree_rankings(tree, rankings):
    ranks_in_node = list()
    if tree.get_attribute('node_level') == 'otu_name':
        otu_idx = tree.get_attribute('otu_index')
        otu_rank = rankings[otu_idx]
        ranks_in_node.append(otu_rank)
    else:
        for child_tree in tree.get_children():
            _aggregate_tree_rankings(child_tree, rankings)
            child_ranks_in_node = child_tree.get_attribute('ranks_in_node')
            for i in child_ranks_in_node:
                ranks_in_node.append(i)
        ranks_in_node.sort()
    tree.set_attribute('ranks_in_node', ranks_in_node)
    return tree

def _derive_rankings_by_otu_idx(comp_def, otu_defs):
    """
    inverts and transforms the rankings list in comp_def so that 
    instead of it being [rank_i] = otu_nest_id, it's 
    [index_within_tornado_run] = rank_i
    dict of rankings:
    the key/indexes are index_within_tornado_run,
    the values are the ranks of that otu
    """
    otu_eids_in_rank_order = comp_def.get_value('top_fst_ranked_otu_ids')

    otu_defs_by_eid = dict()
    for otu_def in otu_defs:
        eid = otu_def.get_nest_id().get_value()
        otu_defs_by_eid[eid] = otu_def

    rankings_by_otu_idx = dict()
    for i in range(len(otu_defs)):
        rank_i_otu_eid = otu_eids_in_rank_order[i]
        otu_def = otu_defs_by_eid[rank_i_otu_eid]
        tornado_run_idx = otu_def.get_value('index_within_tornado_run')
        rankings_by_otu_idx[tornado_run_idx] = i

    return rankings_by_otu_idx

def generate_random_otu_id_rankings(otu_defs):
    """
    used on the comparison itself, not the tree nodes.
    Input is a list of otu TablelikeEntries for all otus.
    Returns a  list of ints of nest_id's ready to be
    used in 'top_fst_ranked_otu_ids' of api/cohort_comparisons
    """
    nest_ids = list()
    for otu in otu_defs:
        eid = otu.get_nest_id().get_value()
        nest_ids.append(eid)
    shuffle(nest_ids)
    return nest_ids

def generate_random_otu_scores(otu_defs):
    """
    returns a list of floats in descending order.
    """
    scores = list()
    for i in range(len(otu_defs)):
        score = random.gauss(1.0, 0.5)
        score = round(score, 3)
        scores.append(score)

    scores.sort(reverse=True)
    return scores


