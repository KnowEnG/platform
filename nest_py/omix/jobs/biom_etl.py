"""
routines for extracting data from a biom_format table and uploading
to tornado_runs, geno_samples and otus endpoints

tightly coupled to mmbdb_seed_job.py
"""

import biom
from biom.table import Table as BiomTable
from nest_py.core.jobs.jobs_logger import log

import nest_py.omix.data_types.tornado_runs as tornado_runs
import nest_py.omix.data_types.geno_samples as geno_samples
import nest_py.omix.data_types.otus as otus

import nest_py.core.data_types.tablelike_entry as tablelike_entry
from nest_py.omix.jobs.sparse_array import SparseArray

TAXONOMY_LEVELS = otus.TAXONOMY_LEVELS

def load_biom_table(filename, subsample=False):
    biom_table = biom.load_table(filename)

    if subsample:
        #biom_table = biom_table.subsample(500, axis="observation", by_id=False)
        biom_table = biom_table.subsample(100, axis="sample", by_id=True)

    log('biom_table shape: ' + str(biom_table.shape))
    return biom_table

def upload_tornado_run(client_registry, biom_table, tornado_cfg):
    """
    tornado_config must supply string values for 'date_of_run'
    and 'display_name_short'
    """
    tornado_schema = tornado_runs.generate_schema()
    tle = tablelike_entry.TablelikeEntry(tornado_schema)
    tle.set_value('date_of_run', tornado_cfg['date_of_run'])
    tle.set_value('display_name_short', tornado_cfg['display_name_short'])
    num_samples = biom_table.length(axis='sample')
    num_otus = biom_table.length(axis='observation')
    tle.set_value('num_samples', num_samples)
    tle.set_value('num_otus', num_otus)

    tornado_client = client_registry[tornado_runs.COLLECTION_NAME]
    tle = tornado_client.create_entry(tle)
    assert(not tle is None)
    return tle


def upload_otu_defs(client_registry, biom_table, tornado_run_id):
    """
    pulls the OTU 'observation' ids (indexed names) out of the biom_table
    and creates entries for them on the server. returns the list of OTUs
    with eve_attributes from the server set
    """
    otus_schema = otus.generate_schema()
    otus_client = client_registry[otus.COLLECTION_NAME]

    #make the otu ids into numbers so we can sort them, even though
    #we will need to use them as strings for lookups
    otu_tornado_id_numbers = (sorted(map(int, (biom_table.ids('observation')))))
    otu_defs = list()
    for i in range(len(otu_tornado_id_numbers)):
        otu_tornado_id_number = otu_tornado_id_numbers[i]
        otu_tornado_id = str(otu_tornado_id_number)
        tle = tablelike_entry.TablelikeEntry(otus_schema)
        tle.set_value('tornado_run_id', tornado_run_id)
        tle.set_value('index_within_tornado_run', i)
        tle.set_value('tornado_observation_key', otu_tornado_id)
        otu_name = 'OTU-' + otu_tornado_id
        tle.set_value('otu_name', otu_name)
        taxonomy_atts = extract_taxonomy_of_otu(biom_table, otu_tornado_id)
        for taxa_level in TAXONOMY_LEVELS:
            tle.set_value(taxa_level, taxonomy_atts[taxa_level])
        otu_defs.append(tle)
    otu_defs = otus_client.bulk_create_entries(otu_defs, batch_size=2000)
    assert(not otu_defs is None)
    return otu_defs

def extract_taxonomy_of_otu(biom_table, otu_observation_id):
    """
    extracts the taxonomy levels for a single otu from a
    'metadata' entry of a BiomTable
    returns a dict where the keys are levels from TAXONOMY_LEVELS
    """
    otu_metadata_from_biom_file = biom_table.metadata(
        otu_observation_id, 'observation')
    taxa_atts = dict()
    observed_vals = otu_metadata_from_biom_file['taxonomy']
    for i in range(len(TAXONOMY_LEVELS)):
        level = TAXONOMY_LEVELS[i]
        raw_taxa = observed_vals[i] # should be like 'k__Bacteria' or 'unclassified'
        if raw_taxa == 'unclassified':
            taxa_atts[level] = 'unclassified'
        else:
            #first characters should match
            assert(level[0] == raw_taxa[0])
            taxa = raw_taxa[3:]
            taxa_atts[level] = taxa
    return taxa_atts

def upload_geno_samples(client_registry, biom_table, tornado_run_id, otu_defs):
    """
    uploads basic description of genome sample data from the biom_table
    (one entry per sample). 

    Note: currently does not upload the otu values themselves, as we don't
    support sparse data well yet. (that data is just kept in memory in this
    seed_job)

    returns a dict of tornado_sample_key to TablelikeEntry's that conform to
    the geno_samples schema (with eve_attributes returned by the upload)
    """
    geno_samples_schema = geno_samples.generate_schema()
    geno_samples_client = client_registry[geno_samples.COLLECTION_NAME]

    tornado_sample_keys = biom_table.ids('sample')
    log('num geno_sample ids to upload: ' + str(len(tornado_sample_keys)))
    geno_samples_list = list()
    otu_counts_lookup = dict() #k: sample_key, v: otu_counts_of_sample
    for tornado_sample_key in tornado_sample_keys:
        bt_sample_metadata = biom_table.metadata(tornado_sample_key, 'sample')
        study_key = bt_sample_metadata['Source_mapping_file']
        #study_sample_key = bt_sample_metadata['external']
        #it seems like the mappings file doesn't tell us anything unique... the sample_ids
        #in the biom_table are universally unique, and they exist in the SampleId column of the
        #patient_metadata files
        study_sample_key = tornado_sample_key
        tle = tablelike_entry.TablelikeEntry(geno_samples_schema)
        tle.set_value('tornado_sample_key', tornado_sample_key)
        tle.set_value('study_sample_key', study_sample_key)
        tle.set_value('tornado_run_id' , tornado_run_id)
        tle.set_value('study_key', study_key)
        geno_samples_list.append(tle)

    geno_samples_list = geno_samples_client.bulk_create_entries(geno_samples_list)
    assert(not geno_samples_list is None)

    log('geno_sample defs uploaded')
    log('extracting otu_counts for each geno_sample')
    #for now, add the gross_counts field after we've uploaded to the
    #server. the big data is then available to other analytics but
    #we don't have a good way to POST it yet (TablelikeSchema doesn't handle
    #sparse arrays yet)
    otu_counts_of_samples = _extract_otu_counts_for_samples(biom_table, otu_defs)
    for tle in geno_samples_list:
        sample_tornado_key  = tle.get_value('tornado_sample_key')
        otu_counts_of_sample = otu_counts_of_samples[sample_tornado_key]
        tle.set_value('otu_counts', otu_counts_of_sample)
        rel_abunds_of_sample = _compute_relative_abundances_for_sample(otu_counts_of_sample)
        tle.set_value('otu_frac_abundances', rel_abunds_of_sample)

    geno_samples_lookup = dict()
    for tle in geno_samples_list:
        key = tle.get_value('tornado_sample_key')
        geno_samples_lookup[key] = tle

    return geno_samples_lookup

def _compute_relative_abundances_for_sample(otu_counts_of_sample):
    """
    input SparseArray of the otu_counts (generated by
    _extract_otu_counts_for_samples) for a single sample.
    returns a SparseArray of the same dimenions with relative
    abundance percentage (between 0.0 and 1.0)
    """
    num_otus = len(otu_counts_of_sample)
    rel_abund_sary = SparseArray(num_otus, not_set_value=0.0)
    tally = 0.0
    for i in range(num_otus):
        tally += otu_counts_of_sample.get_value(i)

    for i in range(num_otus):
        count = otu_counts_of_sample.get_value(i)
        if count > 0.0:
            rel_abund = count / tally
            rel_abund_sary.set_value(i, rel_abund)

    return rel_abund_sary

def _extract_otu_counts_for_samples(biom_table, otu_defs):
    """
    creates a dict of sample_tornado_key (str) -> SparseArray (otu counts, 
        where index is based on 'index_within_tornado_run' from the otu_defs)
    """
    #we need to be able to quickly lookup the index_within_tornado_run 
    #when we are given the otu 'observation' id from the biom_table,
    #which we have called 'tornado_observation_key' in the otu_defs
    otu_index_lookup = dict()
    for otu_def in otu_defs:
        otu_key = otu_def.get_value('tornado_observation_key')
        otu_sparse_index = otu_def.get_value('index_within_tornado_run')
        otu_index_lookup[otu_key] = otu_sparse_index

    num_otus = len(otu_defs)
    geno_sample_sparse_array_lookup = dict() #tornado samplekey -> sparse array
    sample_tornado_keys = biom_table.ids('sample')
    for sample_tornado_key in sample_tornado_keys:
        empty_otu_counts = SparseArray(num_otus, not_set_value=0.0)
        geno_sample_sparse_array_lookup[sample_tornado_key] = empty_otu_counts

    #biom_table format allows us to iterate over only the non-zero otu counts
    for (otu_key, sample_tornado_key) in biom_table.nonzero():
        otu_count = biom_table.get_value_by_ids(otu_key, sample_tornado_key)
        otu_idx = otu_index_lookup[otu_key]
        otu_counts_of_sample = geno_sample_sparse_array_lookup[sample_tornado_key]
        otu_counts_of_sample.set_value(otu_idx, otu_count)
        #log('setting otu count [otu_idx][sample_key][count] = ' +
        #    '[' + str(otu_idx) + '][' + sample_tornado_key + 
        #    '][' + str(otu_count) + ']')

    return geno_sample_sparse_array_lookup

    
