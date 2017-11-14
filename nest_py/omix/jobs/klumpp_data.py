"""
Seed job data for Klumpp Pelvic Pain (Control Vs. IC) data
"""
import biom
import numpy
from biom.table import Table as BiomTable
import csv
from nest_py.core.jobs.jobs_logger import log

import nest_py.omix.data_types.otus as otus
import nest_py.core.jobs.box_downloads as box_downloads
import nest_py.core.jobs.file_utils as file_utils
import nest_py.omix.jobs.cohort_etl as cohort_etl

from nest_py.omix.jobs.seed_data import SeedFlavorData

TAXA_URL = 'https://uofi.box.com/shared/static/lfydiavcp42wv6ff6qmwl8hcao1hrr4v.csv'

OTUS_URL = 'https://uofi.box.com/shared/static/limp35613h5fa3nwlz9yhi8jdmjdx4as.csv'

class KlumppSeedData(SeedFlavorData):

    def __init__(self, data_dir, file_owner):
        self.data_dir = data_dir
        self.file_owner = file_owner
        self.biom_table = None
        return

    def get_biom_table(self):
        if self.biom_table is None:
            self.biom_table = load_klumpp_biom_table(self.data_dir, 
                self.file_owner)
        return self.biom_table

    def get_cohort_configs(self):
        return cohort_configs()

    def get_comparison_configs(self):
        return comparison_configs()

    def get_fst_results_cache_url(self, comparison_key):
        fst_urls = fst_cache_urls()
        if comparison_key in fst_urls:
            url = fst_urls[comparison_key]
        else:
            url = None
        return url
    
    def get_tornado_sample_keys(self, cohort_key):
        biom_table = self.get_biom_table()
        
        if cohort_key == 'Klumpp Control':
            sample_keys = cohort_etl.filter_tornado_keys_biom_kvp(
                biom_table, 'Treatment', 'Control')

        elif cohort_key == 'Klumpp IC':
            sample_keys = cohort_etl.filter_tornado_keys_biom_kvp(
                biom_table, 'Treatment', 'IC')

        elif cohort_key == 'Klumpp: IC Patient-4':
            sample_keys = ['ICF4']
        return sample_keys
        

def load_klumpp_biom_table(data_dir, file_owner):

    otus_fn = otus_filename(data_dir)
    taxa_fn = taxa_filename(data_dir)

    box_downloads.download_from_box_no_auth(OTUS_URL, otus_fn,
        file_owner=file_owner)

    box_downloads.download_from_box_no_auth(TAXA_URL, taxa_fn,
        file_owner=file_owner)

    sample_ids, otu_ids = load_ids(otus_fn)

    otu_metadata = construct_otu_metadata(taxa_fn, otu_ids)#taxonomy
    sample_metadata = construct_sample_metadata(otus_fn)#control or ic

    observations_nary = load_data_matrix(otus_fn, sample_ids,
        otu_ids, num_skip_columns=2)

    otu_number_ids = list()
    for otu_id in otu_ids:
        number_id = otu_id.split(' ')[-1]
        int(number_id) #make sure it's an int
        otu_number_ids.append(number_id)

    biom_table = BiomTable(observations_nary, otu_number_ids, sample_ids, 
        otu_metadata, sample_metadata, table_id='Klumpp')

    print('sample ids: ' + str(biom_table.ids(axis='sample')))
    print('otu ids: ' + str(biom_table.ids(axis='observation')))
    return biom_table

def otus_filename(data_dir):
    fn = data_dir + 'klumpp/IC_WT.csv'
    return fn

def taxa_filename(data_dir):
    fn = data_dir + 'klumpp/klumpp_taxonomy_of_otus.csv'
    return fn

def load_ids(data_filename):
    """
    returns a tuple of lists for sample_ids, otu_ids. sample_ids
    are teh first column, otu_ids are the column names excluding the
    first two which are the only non-otu columns
    """
    sample_ids = list()
    otu_ids = list()
    with open(data_filename, 'r') as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        header_row = next(csv_reader)
        for header_label in header_row[2:]:
            otu_id = header_label
            otu_ids.append(otu_id)
        for row in csv_reader:
            sample_id = row[0]
            sample_ids.append(sample_id)
    return (sample_ids, otu_ids)

def construct_sample_metadata(data_filename):
    metadata = list()
    with open(data_filename, 'r') as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        header_row = next(csv_reader)
        for row in csv_reader:
            sample_id = row[0]
            sample_treatment = row[1]
            assert(sample_treatment in ['IC', 'Control'])
            sample_md = dict()
            sample_md['Treatment'] = sample_treatment
            sample_md['sample_id'] = sample_id
            metadata.append(sample_md) 
    return metadata

def construct_otu_metadata(taxa_filename, otu_ids):
    id_field = 'label'
    taxonomies = file_utils.csv_file_to_nested_dict(taxa_filename, id_field)
    for label in taxonomies:
        taxonomies[label]['species'] = 'unclassified'
    
    #the needed format for the biom format is like 'k__Bacteria',
    #except unclassifed is just 'unclassified' regardless of level
    #see biom_etl.extract_taxonomy_of_otu
    metadata = list()
    for otu_id in otu_ids:
        formatted_tax = list()
        for taxa_level in otus.TAXONOMY_LEVELS:
            taxa_name = taxonomies[otu_id][taxa_level]
            if taxa_name == 'unclassifed':
                taxa_formatted = taxa_name
            else:
                taxa_formatted = taxa_level[0] + '__' + taxa_name
            formatted_tax.append(taxa_formatted)
        otu_md = dict()
        otu_md['taxonomy'] = formatted_tax
        metadata.append(otu_md)
    return metadata


def load_data_matrix(data_filename, sample_ids, otu_ids, 
    num_skip_columns=2):
    """
    loads float matrix into n x m numpy array where is
    number otus, m is num samples
    """

    num_samples = len(sample_ids)
    num_otus = len(otu_ids)
    shape = (num_otus, num_samples)
    nary = numpy.zeros(shape, dtype=numpy.float)

    with open(data_filename, 'r') as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        header_row = next(csv_reader)
        sample_idx = 0
        for row in csv_reader:
            for otu_idx in range(num_otus):
                col_idx = otu_idx + num_skip_columns
                nary[otu_idx][sample_idx] = row[col_idx]
            sample_idx += 1
    return nary

def cohort_configs():
    configs = [
        {
            'display_name_short': 'Klumpp Control',
            'display_name_long': 'Klumpp Pelvic Pain: Control',
            'query': '(treatment=Control)'
        },
        {
            'display_name_short': 'Klumpp IC',
            'display_name_long': 'Klumpp Pelvic Pain: IC',
            'query': '(treatment=IC)'
        },
        {
            'display_name_short': 'Klumpp: IC Patient-4',
            'display_name_long': 'Klumpp Pelvic Pain: Patient 4',
            'query': '(sample_id=ICF4)'
        }
    ]
    return configs

def comparison_configs():
    configs = [
        {
            'comparison_key': 'klumpp_ic_control',
            'display_name': 'Klumpp Pelvic Pain: Control vs. IC',
            'baseline_cohort_key': 'Klumpp Control',
            'variant_cohort_key': 'Klumpp IC',
            'patient_cohort_key': 'Klumpp: IC Patient-4'
        }    
    ]
    return configs
 
def fst_cache_urls():
    """
    the keys are the official comparison_keys used for keeping track of
    cached results on box
    """

    url_lookup = {
        #see mayo_mar16_data for example 
        #currently the klump data is small enough that running FST 
        #every time only takes 2 minutes so not going to bother caching
    }

    return url_lookup

