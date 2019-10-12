import nest_py.omix.data_types.cral.feature_variables as feature_variables
import nest_py.omix.data_types.cral.subjects as subjects
import nest_py.omix.data_types.cral.data_batches as data_batches
import nest_py.omix.data_types.cral.feature_collections as feature_collections
import nest_py.omix.data_types.cral.feature_realizations as feature_realizations

def get_schemas():
    schemas = list()
    schemas.append(feature_variables.generate_schema())
    schemas.append(subjects.generate_schema())
    schemas.append(data_batches.generate_schema())
    schemas.append(feature_realizations.generate_schema_numeric())
    schemas.append(feature_realizations.generate_schema_categoric())
    schemas.append(feature_collections.generate_schema())

    registry = dict()
    for schema in schemas:
        name = schema.get_name()
        registry[name] = schema
    return registry

