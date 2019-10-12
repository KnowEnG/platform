"""
Data type for 'features' that can be used in machine learning analyses as
independent or dependent variables.  feature_variables contain metadata
attributes specific to the 'feature_collection' they are part of so that the
features themselves can be queried when constructing a data set to analyze from
the database.
"""

from nest_py.core.data_types.tablelike_schema import TablelikeSchema
from nest_py.core.data_types.tablelike_entry import TablelikeEntry

COLLECTION_NAME = 'feature_variables'

def generate_schema():
    schema = TablelikeSchema(COLLECTION_NAME)

    #the feature_collection that this variable has metadata attributes for
    schema.add_foreignid_attribute('feature_collection_id')

    #the name of the feature within the feature_collection. This is not
    #meant to be unique (even within the collection), but uniqueness is
    #probably a good idea.
    schema.add_categoric_attribute('local_name')

    #feature analysis can only automatically handle these types of columns
    schema.add_categoric_attribute('feature_type', 
        valid_values=['categoric', 'numeric'])

    #the run that loaded this data into the db.TODO: the variable maybe
    #shouldn't be inherently tied to the run? just the realz? variable
    #might be reused
    schema.add_foreignid_attribute('wix_run_id')

    #all feature_variables from the same feature_collection should #have
    #metadata tles that share the same nested schema here. The entries will then
    #all have the same keys (eg. all feature_variables that are otus will have
    #entries for the otus schema here, and then those entries will be queryable
    #against each other using metadata_attributes).  TODO: the entries will be
    #complete tles, should there be a tle type? For now we'll use the method
    #TablelikeSchema.object_to_flat_jdata(tle) to create the json payload we
    #store here
    schema.add_json_attribute('metadata_attributes')

    return schema

