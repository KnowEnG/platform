import nest_py.knoweng.data_types.analysis_networks as analysis_networks
import nest_py.knoweng.data_types.collections as collections
import nest_py.knoweng.data_types.files as files
import nest_py.knoweng.data_types.feature_prioritizations as feature_prioritizations
import nest_py.knoweng.data_types.gene_set_characterizations as gene_set_characterizations
import nest_py.knoweng.data_types.jobs as jobs
import nest_py.knoweng.data_types.projects as projects
import nest_py.knoweng.data_types.public_gene_sets as public_gene_sets
import nest_py.knoweng.data_types.sample_clusterings as sample_clusterings
import nest_py.knoweng.data_types.signature_analyses as signature_analyses
import nest_py.knoweng.data_types.species as species
import nest_py.knoweng.data_types.ssviz_jobs_spreadsheets as ssviz_jobs_spreadsheets
import nest_py.knoweng.data_types.ssviz_spreadsheets as ssviz_spreadsheets
import nest_py.knoweng.data_types.ssviz_feature_data as ssviz_feature_data
import nest_py.knoweng.data_types.ssviz_feature_variances as ssviz_feature_variances
import nest_py.knoweng.data_types.ssviz_feature_correlations as ssviz_feature_correlations


def get_schemas():
    schemas = list()
    schemas.append(analysis_networks.generate_schema())
    schemas.append(collections.generate_schema())
    schemas.append(files.generate_schema())
    schemas.append(feature_prioritizations.generate_schema())
    schemas.append(gene_set_characterizations.generate_schema())
    schemas.append(jobs.generate_schema())
    schemas.append(projects.generate_schema())
    schemas.append(public_gene_sets.generate_schema())
    schemas.append(sample_clusterings.generate_schema())
    schemas.append(signature_analyses.generate_schema())
    schemas.append(species.generate_schema())
    schemas.append(ssviz_jobs_spreadsheets.generate_schema())
    schemas.append(ssviz_spreadsheets.generate_schema())
    schemas.append(ssviz_feature_data.generate_schema())
    schemas.append(ssviz_feature_variances.generate_schema())
    schemas.append(ssviz_feature_correlations.generate_schema())

    schema_registry = dict()
    for schema in schemas:
        nm = schema.get_name()
        schema_registry[nm] = schema
    return schema_registry
