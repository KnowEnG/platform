"""
Data type for a 'subject' in a medical sense. Usually a human
or a patient. This does not uniquely identify a sample or a
attribute by itself. In the most general sense, a unique attribute is
defined by a [subject, timestamp, feature], but we normally
only identify a realization by a [subject, feature].
"""

from nest_py.core.data_types.tablelike_schema import TablelikeSchema
from nest_py.core.data_types.tablelike_entry import TablelikeEntry

COLLECTION_NAME = 'subjects'

def generate_schema():
    schema = TablelikeSchema(COLLECTION_NAME)

    #keyspace: an identifier for a group of subjects who have
    #unique keys relative to one another. Something like
    #'mayo_march2016_microbiome_study'
    schema.add_categoric_attribute('key_space')

    #official key for the subject. If multiple data sources
    #have slightly different identifiers e.g. ('patient-22', 
    #'p22', '22', 'id-22'), this is the official key that those
    #will need to be mapped to when loading the data into the db.
    schema.add_categoric_attribute('official_key')

    #an identifier of the job run that originally created this subject entry.
    #there is no restriction on what type of job might have created it
    schema.add_foreignid_attribute('wix_run_id')

    return schema

