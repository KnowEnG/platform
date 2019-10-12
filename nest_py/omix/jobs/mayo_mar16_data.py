"""
Seed job data for combined data set from Mayo (data handoff was March 2016)
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
import nest_py.omix.jobs.patient_data_etl as patient_data_etl
import nest_py.omix.jobs.biom_etl as biom_etl
from nest_py.omix.jobs.seed_data import SeedFlavorData

#this script will download the biom_file at the following url and write
#it to BIOM_FILE_NAME
BIOM_FILE_BOX_URL = 'https://uofi.box.com/shared/static/hwkkya44jn07eo1y26jm6h2vcnrlg74r.biom'
BIOM_FILE_NAME = 'PatientVis_Mar16/Paired/test_paired.biom'

#only do the cdiff+ and cdiff- cohorts, and their comparison
CDIFF_ONLY = False

class MayoMar16SeedData(SeedFlavorData):

    def __init__(self, data_dir, file_owner, subsample=False):
        self.data_dir = data_dir
        self.file_owner = file_owner
        self.biom_table = None
        self.patient_data = None
        self.subsample = subsample
        return

    def get_username(self):
        return 'mayo-shared'

    def get_userpass(self):
        return 'VisualAnalytics'

    def get_biom_table(self):
        if self.biom_table is None:
            dest_filename = self.data_dir + '/' + BIOM_FILE_NAME
            print('biom download location: ' + dest_filename)

            box_downloads.download_from_box_no_auth(
                BIOM_FILE_BOX_URL, dest_filename,
                file_owner=self.file_owner, force=False)

            self.biom_table = biom_etl.load_biom_table(
                dest_filename, subsample=self.subsample)

        return self.biom_table

    def get_cohort_configs(self):
        return cohort_configs()

    def get_comparison_configs(self):
        return comparison_configs()

    def get_tornado_config(self):
        return tornado_config()

    def get_fst_results_cache_url(self, comparison_key):
        fst_urls = fst_cache_urls()

        if comparison_key in fst_urls:
            url = fst_urls[comparison_key]
        else:
            url = None
        return url
    
    def get_tornado_sample_keys(self, cohort_key):
        biom_table = self.get_biom_table()
        all_patient_data = self.get_patient_data()

        if cohort_key == 'MWR1':
            tornado_keys = cohort_etl.filter_tornado_keys_biom_kvp(
                biom_table, 'Source_mapping_file', 'MWR1')

        elif cohort_key == 'MWR2':
            tornado_keys = cohort_etl.filter_tornado_keys_biom_kvp(
                biom_table, 'Source_mapping_file', 'MWR2')

        elif cohort_key == 'Tissue=Stool':
            tornado_keys = cohort_etl.filter_tornado_keys_biom_kvp(
                biom_table, 'Tissue', 'Stool')

        elif cohort_key == 'Tissue=Nasal':
            tornado_keys = cohort_etl.filter_tornado_keys_biom_kvp(
                biom_table, 'Tissue', 'Nasal')

        elif cohort_key == 'Tissue=Cervical':
            tornado_keys = cohort_etl.filter_tornado_keys_biom_kvp(
                biom_table, 'Tissue', 'Cervical')

        elif cohort_key == 'C. diff +':
            tornado_keys = cohort_etl.filter_tornado_keys_patient_data_kvp(
                all_patient_data, 'Cdiff', 'cdiff_level', 'positive')

        elif cohort_key == 'C. diff -':
            tornado_keys = cohort_etl.filter_tornado_keys_patient_data_kvp(
                all_patient_data, 'Cdiff', 'cdiff_level', 'negative')

        elif cohort_key == 'C. diff Normal':
            tornado_keys = cohort_etl.filter_tornado_keys_patient_data_kvp(
                all_patient_data, 'Cdiff', 'cdiff_level', 'normal')

        elif cohort_key == 'Pardi:Patient-1':
            tornado_keys = ['ssx1']

        elif cohort_key == 'CRC: Diagnosis=Normal':
            tornado_keys = cohort_etl.filter_tornado_keys_patient_data_kvp(
                all_patient_data, 'CRC_adenoma', 'Diagnosis', 'normal')
            
        elif cohort_key == 'CRC: Diagnosis=Cancer':
            tornado_keys = cohort_etl.filter_tornado_keys_patient_data_kvp(
                all_patient_data, 'CRC_adenoma', 'Diagnosis', 'cancer')

        elif cohort_key == 'CRC: Diagnosis=Adenoma':
            tornado_keys = cohort_etl.filter_tornado_keys_patient_data_kvp(
                all_patient_data, 'CRC_adenoma', 'Diagnosis', 'adenoma')

        elif cohort_key == 'CRC: Polyps=True':
            tornado_keys = cohort_etl.filter_tornado_keys_patient_data_kvp(
                all_patient_data, 'CRC_adenoma', 'POLYP.1=Y', '1')

        elif cohort_key == 'CRC: Polyps=False':
            tornado_keys = cohort_etl.filter_tornado_keys_patient_data_kvp(
                all_patient_data, 'CRC_adenoma', 'POLYP.1=Y', '0')

        elif cohort_key == 'Lambert: Day 0':
            tornado_keys = cohort_etl.filter_tornado_keys_patient_data_kvp(
                all_patient_data, 'Lambert_Nathaniel', 'days_since_vaccine', '0')

        elif cohort_key == 'Lambert: Day 7':
            tornado_keys = cohort_etl.filter_tornado_keys_patient_data_kvp(
                all_patient_data, 'Lambert_Nathaniel', 'days_since_vaccine', '7')

        elif cohort_key == 'Lambert: Day 28':
            tornado_keys = cohort_etl.filter_tornado_keys_patient_data_kvp(
                all_patient_data, 'Lambert_Nathaniel', 'days_since_vaccine', '28')

        elif cohort_key == 'Taneja: RA Patients':
            tornado_keys = cohort_etl.filter_tornado_keys_patient_data_kvp(
                all_patient_data, 'Taneja_RA_Normal_Relatives', 'is_patient', True)

        elif cohort_key == 'Taneja: Relatives':
            tornado_keys = cohort_etl.filter_tornado_keys_patient_data_kvp(
                all_patient_data, 'Taneja_RA_Normal_Relatives', 'is_family', True)
        else:
            raise Exception("Don't know about cohort : " +
                str(cohort_key) + ". Can't query samples for it")
        return tornado_keys

    def get_patient_data(self):
        if self.patient_data is None:
            self.patient_data = patient_data_etl.load_all_metadata(
                self.data_dir)
        return self.patient_data
 
def cohort_configs():
    cdiff_configs = [
        {
            'display_name_short': 'C. diff +',
            'display_name_long': 'C. diff Positive from Pardi Study',
            'query': '(cdiff_level=positive)'
        },
        {
            'display_name_short': 'C. diff -',
            'display_name_long': 'C. diff Negative from Pardi Study',
            'query': '(cdiff_level=negative)'
        },
        {
            'display_name_short': 'Pardi:Patient-1',
            'display_name_long': 'Patient 1, Pardi Study',
            'query': '((study=Cdiff) and (tornado_sample_key=ssx1))'
        }

    ]

    noncdiff_configs = [
        {
            'display_name_short': 'MWR1',
            'display_name_long': 'MidwestReference-1',
            'query': '(study_key=MWR1)'
        },
        {
            'display_name_short': 'C. diff Normal',
            'display_name_long': 'C. diff Normal from Pardi Study',
            'query': '(cdiff_level=normal)'
        },
        {
            'display_name_short': 'MWR2',
            'display_name_long': 'MidwestReference-2',
            'query': '(study_key=MWR2)'
        },
#        {
#            'display_name_short': 'Tissue=Stool',
#            'display_name_long': 'All Stool Samples, All Studies',
#            'query': '(Tissue=Stool)'
#        },
        {
            'display_name_short': 'Tissue=Nasal',
            'display_name_long': 'All Nasal Samples, All Studies',
            'query': '(Tissue=Nasal)'
        },
        {
            'display_name_short': 'Tissue=Cervical',
            'display_name_long': 'All Cervical Samples, All Studies',
            'query': '(Tissue=Cervical)'
        },
        {
            'display_name_short': 'CRC: Diagnosis=Normal',
            'display_name_long': 'CRC Adenoma Study: Diagnosis Normal',
            'query': '((study_key=CRC_adenoma)and(Diagnosis=normal))'
        },
        {
            'display_name_short': 'CRC: Diagnosis=Cancer',
            'display_name_long': 'CRC Adenoma Study: Diagnosis Cancer',
            'query': '((study_key=CRC_adenoma)and(Diagnosis=Cancer))'
        },
        {
            'display_name_short': 'CRC: Diagnosis=Adenoma',
            'display_name_long': 'CRC Adenoma Study: Diagnosis Adenoma',
            'query': '((study_key=CRC_adenoma)and(Diagnosis=Adenoma))'
        },
        {
            'display_name_short': 'CRC: Polyps=True',
            'display_name_long': 'CRC Adenoma Study: One or More Polyps',
            'query': '((study_key=CRC_adenoma)and(Polyps=True))'
        },
        {
            'display_name_short': 'CRC: Polyps=False',
            'display_name_long': 'CRC Adenoma Study: Zero Polyps',
            'query': '((study_key=CRC_adenoma)and(Polyps=False))'
        },
        {
            'display_name_short': 'Lambert: Day 0',
            'display_name_long': 'Lambert Nasal: Days Since Vaccine = 0',
            'query': '((study_key=Lambert)and(days_since_vaccine=0))'
        },
        {
            'display_name_short': 'Lambert: Day 7',
            'display_name_long': 'Lambert Nasal: Days Since Vaccine = 7',
            'query': '((study_key=Lambert)and(days_since_vaccine=7))'
        },
        {
            'display_name_short': 'Lambert: Day 28',
            'display_name_long': 'Lambert Nasal: Days Since Vaccine = 28',
            'query': '((study_key=Lambert)and(days_since_vaccine=28))'
        },
        {
            'display_name_short': 'Taneja: RA Patients',
            'display_name_long': 'Taneja: Rheumatiod Arthritis Patient',
            'query': '((study_key=Taneja)and(is_patient=True))'
        },
        {
            'display_name_short': 'Taneja: Relatives',
            'display_name_long': 'Taneja: RA Normal Relatives',
            'query': '((study_key=Taneja)and(is_family=True))'
        }
    ]

    if CDIFF_ONLY:
        configs = cdiff_configs
    else:
        configs = cdiff_configs + noncdiff_configs
    return reversed(configs)


def comparison_configs():
    """
    _cohort_keys are display_name_short of the cohort
    """
    cdiff_configs = [
        {
            'comparison_key': 'cdiff_neg_pos',
            'display_name': 'C. diff - vs. C. diff +, Pardi Study',
            'baseline_cohort_key': 'C. diff -',
            'variant_cohort_key': 'C. diff +',
            'patient_cohort_key': 'Pardi:Patient-1'
        }    
    ]
    noncdiff_configs = [
        {
            'comparison_key': 'mwr1_mwr2',
            'display_name': 'MWR 1 vs. MWR 2',
            'baseline_cohort_key': 'MWR1',
            'variant_cohort_key': 'MWR2',
            'patient_cohort_key': 'Pardi:Patient-1'
        },
        {
            'comparison_key': 'cdiff_norm_pos',
            'display_name': 'Normal vs. C. diff +, Pardi Study',
            'baseline_cohort_key': 'C. diff Normal',
            'variant_cohort_key': 'C. diff +',
            'patient_cohort_key': 'Pardi:Patient-1'
        },
#        {
#            'comparison_key': 'stool_nasal',
#            'display_name': 'All Stool vs. All Nasal',
#            'baseline_cohort_key': 'Tissue=Stool',
#            'variant_cohort_key': 'Tissue=Nasal',
#            'patient_cohort_key': 'Pardi:Patient-1'
#        },
#        {
#            'comparison_key': 'stool_cervical',
#            'display_name': 'All Stool vs. All Cervical',
#            'baseline_cohort_key': 'Tissue=Stool',
#            'variant_cohort_key': 'Tissue=Cervical',
#            'patient_cohort_key': 'Pardi:Patient-1'
#        },
        {
            'comparison_key': 'nasal_cervical',
            'display_name': 'All Nasal vs. All Cervical',
            'baseline_cohort_key': 'Tissue=Nasal',
            'variant_cohort_key': 'Tissue=Cervical',
            'patient_cohort_key': 'Pardi:Patient-1'
        },
        {
            'comparison_key': 'crc_cancer',
            'display_name': 'CRC: Normal vs. Cancer',
            'baseline_cohort_key': 'CRC: Diagnosis=Normal',
            'variant_cohort_key': 'CRC: Diagnosis=Cancer',
            'patient_cohort_key': 'Pardi:Patient-1'
        },
        {
            'comparison_key': 'crc_adenoma',
            'display_name': 'CRC: Normal vs. Adenoma',
            'baseline_cohort_key': 'CRC: Diagnosis=Normal',
            'variant_cohort_key': 'CRC: Diagnosis=Adenoma',
            'patient_cohort_key': 'Pardi:Patient-1'
        },
        {
            'comparison_key': 'crc_polyps',
            'display_name': 'CRC: No Polyps vs. Polyps',
            'baseline_cohort_key': 'CRC: Polyps=False',
            'variant_cohort_key': 'CRC: Polyps=True',
            'patient_cohort_key': 'Pardi:Patient-1'
        },
        {
            'comparison_key': 'lambert_7days',
            'display_name': 'Lambert Vaccine: 7 days',
            'baseline_cohort_key': 'Lambert: Day 0',
            'variant_cohort_key': 'Lambert: Day 7',
            'patient_cohort_key': 'Pardi:Patient-1'
        },
        {
            'comparison_key': 'lambert_28days',
            'display_name': 'Lambert Vaccine: 28 days',
            'baseline_cohort_key': 'Lambert: Day 0',
            'variant_cohort_key': 'Lambert: Day 28',
            'patient_cohort_key': 'Pardi:Patient-1'
        },
        {
            'comparison_key': 'taneja_relatives',
            'display_name': 'Taneja: RA Patients vs. Relatives',
            'baseline_cohort_key': 'Taneja: RA Patients',
            'variant_cohort_key': 'Taneja: Relatives',
            'patient_cohort_key': 'Pardi:Patient-1'
        }

    ]
    
    if CDIFF_ONLY:
        configs = cdiff_configs
    else:
        configs = cdiff_configs + noncdiff_configs
    return reversed(configs)

def tornado_config():
    config = {
        'date_of_run' : '2016-03-16T00:00:00Z',
        'display_name_short' : 'Mayo_16Mar2016'
    }
    return config

def fst_cache_urls():
    """
    the keys are the official comparison_keys used for keeping track of
    cached results on box
    """

    url_lookup = {
        #using DEBUG_CONFIG. these are commented out in the comparison_configs
        #and arent' being used. they would take days to run with full config
        'stool_cervical': 'https://uofi.box.com/shared/static/j3v2sdhu1iaqw8k2zojfxp47ngxcyh95.csv',
        'stool_nasal': 'https://uofi.box.com/shared/static/oqkzo7uo5s4m20vk8a5mdwnu9c4d1r22.csv',

        #using full-accuracy config
        'cdiff_neg_pos': 'https://uofi.box.com/shared/static/nqe468f86in0opd9ugouroahw2niwmai.csv',
        'cdiff_norm_pos': 'https://uofi.box.com/shared/static/y37xji79tsupkzvn9hqshtxrofj3ukxu.csv',
        'mwr1_mwr2' :'https://uofi.box.com/shared/static/wm31j5btzf2vkyg6mktkvkxysdm1b44p.csv',
        'nasal_cervical': 'https://uofi.box.com/shared/static/k2oi8hp3p8dgpa4jle3iycfnsikd5owa.csv',
        'crc_polyps': 'https://uofi.box.com/shared/static/mdtphlqmi8bd2rop5psi2a4j9gia3ye8.csv',
        'crc_cancer': 'https://uofi.box.com/shared/static/dkj7n8q491ww32ue7caed9ly2k7l6nsw.csv',
        'crc_adenoma': 'https://uofi.box.com/shared/static/zqnhvhrab9bz2rvi4w15k0vnxjm9e6xs.csv',
        'lambert_7days': 'https://uofi.box.com/shared/static/vm5sp5zw53ynytcbkeua6c62cj5osf3r.csv',
        'lambert_28days': 'https://uofi.box.com/shared/static/ftbuoacv0cyh8p6ginq6cn2p27815ezj.csv',
        'taneja_relatives': 'https://uofi.box.com/shared/static/s7kl41hkm25lj1tyvd0f5s8f7o1l5hr5.csv',
    }

    return url_lookup


