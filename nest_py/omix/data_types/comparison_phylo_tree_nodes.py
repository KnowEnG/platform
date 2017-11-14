"""
Phylogenetic Tree Nodes (Taxonomy Nodes) for a Cohort Comparison.
For each node in the tree, there is an entry in the 
compairson_phylo_tree_nodes endpoint that provides data about
that point in the tree related to the Comparison of the cohorts involved,
but does not have the basic information about the individual cohorts at
that point.

see also cohort_phylo_tree_nodes for data about the nodes for individual cohorts

see also comparison_phylo_tree_structure for the data on how the
 tree nodes here are nested together.

"""
from nest_py.core.data_types.tablelike_schema import TablelikeSchema

COLLECTION_NAME = 'comparison_phylo_tree_nodes'

def generate_schema():
    schema = TablelikeSchema(COLLECTION_NAME)
    schema.add_foreignid_attribute('comparison_id')
    schema.add_categoric_attribute('node_level', valid_values=None)
    schema.add_categoric_attribute('node_name', valid_values=None)
    schema.add_numeric_attribute('node_idx', min_val=0)
    schema.add_numeric_attribute('parent_node_idx', min_val=-1)

    schema.add_numeric_list_attribute('top_fst_otu_rankings_in_node')

    schema.add_index(['comparison_id', 'node_level'])
    schema.add_index(['comparison_id', 'parent_node_idx'])
    return schema


