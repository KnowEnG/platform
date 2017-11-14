import nest_py.knoweng.data_types.analysis_networks as analysis_networks
import nest_py.knoweng.data_types.collections as collections 
import nest_py.knoweng.data_types.files as files 
import nest_py.knoweng.data_types.gene_prioritizations as gene_prioritizations
import nest_py.knoweng.data_types.gene_set_characterizations as gene_set_characterizations
import nest_py.knoweng.data_types.jobs as jobs
import nest_py.knoweng.data_types.projects as projects 
import nest_py.knoweng.data_types.public_gene_sets as public_gene_sets
import nest_py.knoweng.data_types.sample_clusterings as sample_clusterings
import nest_py.knoweng.data_types.species as species

def get_schemas():
    schemas = list()
    schemas.append(analysis_networks.generate_schema())
    schemas.append(collections.generate_schema())
    schemas.append(files.generate_schema())
    schemas.append(gene_prioritizations.generate_schema())
    schemas.append(gene_set_characterizations.generate_schema())
    schemas.append(jobs.generate_schema())
    schemas.append(projects.generate_schema())
    schemas.append(public_gene_sets.generate_schema())
    schemas.append(sample_clusterings.generate_schema())
    schemas.append(species.generate_schema())

    schema_registry = dict()
    for schema in schemas:
        nm = schema.get_name()
        schema_registry[nm] = schema
    return schema_registry
