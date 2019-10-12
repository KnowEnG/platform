"""
A feature_collection is a set of features that share the same 
metadata fields. OTUs would be an example of features that all have the
same metadata for things like tornado_run, species name, etc.
The features in in a feature_collection are normally loaded into the
database (as feature_variables) at the same time as the 
feature_collection entry itself.
"""

from nest_py.core.data_types.tablelike_schema import TablelikeSchema
from nest_py.core.data_types.tablelike_entry import TablelikeEntry


COLLECTION_NAME = 'feature_collections'

def generate_schema():
    schema = TablelikeSchema(COLLECTION_NAME)

    schema.add_categoric_attribute('collection_name')
    
    #while this is no good for querying, will probably be
    #important once users are uploading arbitrary spreadsheets
    schema.add_categoric_attribute('description')

    #an object-blob of a schema. The attributes of the schema
    #are the metadata attributes that all feature_variables in
    #the feature_collection will contain. E.g. for the 
    #'otus' feature_collection, each feature_variable is an otu
    #and the metadata_schema will have things like 'tornado_run_id'
    #and 'otu_number' and maybe 'short_taxa_name'
    schema.add_json_attribute('metadata_schema')

    schema.add_foreignid_attribute('wix_run_id')
    return schema

