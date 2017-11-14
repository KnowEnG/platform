
import nest_py.omix.data_types.cohort_comparisons as cohort_comparisons
import nest_py.omix.data_types.cohort_phylo_tree_nodes as cohort_phylo_tree_nodes
import nest_py.omix.data_types.cohorts as cohorts
import nest_py.omix.data_types.comparison_phylo_tree_nodes as comparison_phylo_tree_nodes
import nest_py.omix.data_types.geno_samples as geno_samples
import nest_py.omix.data_types.otus as otus
import nest_py.omix.data_types.tornado_runs as tornado_runs

def get_schemas():
    schemas = list()
    schemas.append(cohort_comparisons.generate_schema())
    schemas.append(cohort_phylo_tree_nodes.generate_schema())
    schemas.append(cohorts.generate_schema())
    schemas.append(comparison_phylo_tree_nodes.generate_schema())
    schemas.append(geno_samples.generate_schema())
    schemas.append(otus.generate_schema())
    schemas.append(tornado_runs.generate_schema())

    registry = dict()
    for schema in schemas:
        name = schema.get_name()
        registry[name] = schema
    return registry

