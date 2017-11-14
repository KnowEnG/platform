"""
Schema and Endpoint for storing OTU descriptions per tornado run.
This doesn't store any data, just the names of the OTUs, which normally
look like "OTU-23", but need not be continously label (OTUs are sometimes
dropped by tornado, it seems, and not re-numbered to cover the gaps)
"""

from nest_py.core.data_types.tablelike_schema import TablelikeSchema

COLLECTION_NAME = 'otus'

TAXONOMY_LEVELS = ['kingdom', 'phylum', 'class', 'order', 'family', 'genus', 'species']

def generate_schema():
    schema = TablelikeSchema(COLLECTION_NAME)
    schema.add_foreignid_attribute('tornado_run_id')
    schema.add_numeric_attribute('index_within_tornado_run', min_val=0, max_val=None)
    #the 'id' of the otu as an observation in the biom_table associated with the tornado
    #run
    schema.add_categoric_attribute('tornado_observation_key', valid_values=None)
    schema.add_categoric_attribute('otu_name', valid_values=None)
    for taxa_level in TAXONOMY_LEVELS:
        schema.add_categoric_attribute(taxa_level, valid_values=None)

    return schema

