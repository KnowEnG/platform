"""
Seed job data for Klumpp Project 2. There is a baseclass (KlumppIc2SeedData) that
defines the template for this batch of data. There are then 4 implementation classes,
one for each tornado run (Lizzie, Webin Fecal, Webin Cecum, Webin Combined)
"""
import biom
import numpy
from biom.table import Table as BiomTable
import csv
import os
from nest_py.core.jobs.jobs_logger import log

import nest_py.omix.data_types.otus as otus
import nest_py.core.jobs.box_downloads as box_downloads
import nest_py.core.jobs.file_utils as file_utils
import nest_py.omix.jobs.cohort_etl as cohort_etl
import nest_py.omix.jobs.biom_etl as biom_etl
import nest_py.omix.jobs.patient_data_etl as patient_data_etl

from nest_py.omix.jobs.seed_data import SeedFlavorData

BIOM_BOX_URL_LIZZIE = 'https://uofi.box.com/shared/static/6vufgz1ptegi2ki4c4slm18srkk63zyp.biom'
BIOM_BOX_URL_WENBIN_CECUM = 'https://uofi.box.com/shared/static/9ytinrd5rbr25zg7359imkd8esgjug5b.biom'
BIOM_BOX_URL_WENBIN_FECAL = 'https://uofi.box.com/shared/static/rzupi40fq5ej1r3r4n4y67evofhznnr8.biom'
BIOM_BOX_URL_WENBIN_COMBINED = 'https://uofi.box.com/shared/static/kuvepl6p1db67lyw30osrkox4vltum64.biom'

METADATA_BOX_URL = 'https://uofi.box.com/shared/static/wg7d8jsw75we0fx3ogconwneos6ssdfe.csv'

class KlumppIC2SeedData(SeedFlavorData):
    """
    this is an abstract class that the lizzie and wenbin
    data sets implement (one SeedFlavorData class per
    .biom file)
    """

    def __init__(self, data_dir, file_owner):
        self.data_dir = os.path.join(data_dir, 'klumpp_ic2')
        self.file_owner = file_owner
        self.biom_table = None
        self.patient_metadata = None
        return

    def get_username(self):
        return 'klumpplab'

    def get_userpass(self):
        return 'VisualAnalytics2017'

    def get_biom_table(self):
        if self.biom_table is None:
            
            dest_filename = os.path.join(self.data_dir, self.get_biom_basename())
            print('biom download location: ' + dest_filename)

            biom_file_box_url = self.get_biom_file_box_url()
            box_downloads.download_from_box_no_auth(
                biom_file_box_url, dest_filename,
                file_owner=self.file_owner, force=False)

            self.biom_table = biom_etl.load_biom_table(
                dest_filename, subsample=False)

        return self.biom_table

    def get_biom_file_box_url(self):
        raise "Not Implemented"
        return None

    def get_patient_metadata(self):
        if self.patient_metadata is None:
            fn = os.path.join(self.data_dir, '15_September_2017_Fecal_and_Cecum_Extractions_pdg_IDs.csv')
            log('Ensuring download for: ' + fn)
            box_downloads.download_from_box_no_auth(
                METADATA_BOX_URL, fn,
                file_owner=self.file_owner, force=False)
            log('Reading csv: ' + fn)
            row_data = file_utils.csv_file_to_nested_dict(fn, 'ID-pdg')

            self.patient_metadata = dict()
            for x in ['lizzie_fecal', 'wenbin_fecal', 'wenbin_cecum']:
                self.patient_metadata[x] = patient_data_etl.init_study_data()
            for tornado_key in row_data:
                row = row_data[tornado_key]
                study_key = None
                if row['Lab'] == 'Lizzie':
                    study_key = 'lizzie_fecal'
                elif row['Lab'] == 'Webbin': #this mistake is in the csv
                    if row['Sample Type'] == 'Fecal':
                        study_key = 'wenbin_fecal'
                    elif row['Sample Type'] == 'Cecum':
                        study_key = 'wenbin_cecum'
                else:
                    log('Failed to identify study_key, [lab][sample type] = [' +
                        row['Lab'] + '][' + row['Sample Type'] + ']')
                if not study_key is None:
                    self.patient_metadata[study_key]['patients'][tornado_key] = row   
            log('Returning patient metadata')

        return self.patient_metadata

    def get_biom_basename(self):
        raise("Not Implemented")
        return None

class LizzieSeedData(KlumppIC2SeedData):

    def get_biom_basename(self):
        basename = 'lizzie_paired.biom'
        return basename

    def get_biom_file_box_url(self):
        return BIOM_BOX_URL_LIZZIE

    def get_cohort_configs(self):
        configs = [
        {
            'display_name_short': 'Lizzie Wildtype',
            'display_name_long': 'Lizzie Fecal Wild-type(B6)',
            'query': '((Lab=Lizzie) and (Sample Type=Fecal) and (Genotype=Wild-type(B6)))'
        },
        {
            'display_name_short': 'Lizzie Fecal AOAH -/-',
            'display_name_long': 'Lizzie Fecal AOAH -/-',
            'query': '((Lab=Lizzie) and (Sample Type=Fecal) and (Genotype=AOAH -/-))'
        },
        {
            'display_name_short': 'Lizzie Fecal AOAH -/-, AhR R/R, CRF cre/+',
            'display_name_long': 'Lizzie Fecal AOAH -/-, AhR R/R, CRF cre/+',
            'query': '((Lab=Lizzie) and (Sample Type=cal) and (Genotype=AOAH /, AhR R/R, CRF cre/+))'
        },
        {
            'display_name_short': 'Lizzie Fecal Ppar +/R, CRF cre/+, AOAH -/-',
            'display_name_long': 'Lizzie Fecal Ppar +/R, CRF cre/+, AOAH -/-',
            'query': '((Lab=Lizzie) and (Sample Type=Fecal) and (Genotype=Ppar +/R, CRF cre/+, AOAH -/-))'
        },
        {
            'display_name_short': 'Lizzie Fecal Ppar +/+, CRF cre/+',
            'display_name_long': 'Lizzie Fecal Ppar +/+, CRF cre/+',
            'query': '((Lab=Lizzie) and (Sample Type=Fecal) and (Genotype=Ppar +/+, CRF cre/+))'
        },
        {
            'display_name_short': 'Lizzie Patient 1',
            'display_name_long': 'Lizzie Patient 1',
            'query': '((Lab=Lizzie) and (Sample Type=Fecal) and (ID=1-A1-WT1))'
        }
        ]
        return configs

    def get_comparison_configs(self):
        configs = [
        {
            'comparison_key': 'lizzie_AOAH',
            'display_name': 'Lizzie: Wildtype vs. AOAH -/-',
            'baseline_cohort_key': 'Lizzie Wildtype',
            'variant_cohort_key': 'Lizzie Fecal AOAH -/-',
            'patient_cohort_key': 'Lizzie Patient 1'
        },    
        {
            'comparison_key': 'lizzie_AhR',
            'display_name': 'Lizzie: Wildtype vs. AOAH -/-, AhR R/R, CRF cre/+',
            'baseline_cohort_key': 'Lizzie Wildtype',
            'variant_cohort_key': 'Lizzie Fecal AOAH -/-, AhR R/R, CRF cre/+',
            'patient_cohort_key': 'Lizzie Patient 1'
        },
        {
            'comparison_key': 'lizzie_Ppar+R',
            'display_name': 'Lizzie: Wildtype vs. Ppar +/R, CRF cre/+, AOAH -/-',
            'baseline_cohort_key': 'Lizzie Wildtype',
            'variant_cohort_key': 'Lizzie Fecal Ppar +/R, CRF cre/+, AOAH -/-',
            'patient_cohort_key': 'Lizzie Patient 1'
        },        
        {
            'comparison_key': 'lizzie_Ppar++',
            'display_name': 'Lizzie: Wildtype vs. Ppar +/+, CRF cre/+',
            'baseline_cohort_key': 'Lizzie Wildtype',
            'variant_cohort_key': 'Lizzie Fecal Ppar +/+, CRF cre/+',
            'patient_cohort_key': 'Lizzie Patient 1'
        }
        ]
        return configs

    def get_tornado_config(self):
        config = {
            'date_of_run': '2018-02-23T00:00:00Z',
            'display_name_short': 'lizzie_paired'
        }
        return config

    def get_fst_results_cache_url(self, comparison_key): 
        return None

    def get_tornado_sample_keys(self, cohort_key):
        patient_metadata = self.get_patient_metadata()
        
        if cohort_key == 'Lizzie Wildtype':
            sample_keys = cohort_etl.filter_tornado_keys_patient_data_kvp(
                patient_metadata, 'lizzie_fecal', 'Genotype', 'Wild-type(B6)')

        elif cohort_key == 'Lizzie Fecal AOAH -/-':
            sample_keys = cohort_etl.filter_tornado_keys_patient_data_kvp(
                patient_metadata, 'lizzie_fecal', 'Genotype', 'AOAH -/-')

        elif cohort_key == 'Lizzie Fecal AOAH -/-, AhR R/R, CRF cre/+':
            sample_keys = cohort_etl.filter_tornado_keys_patient_data_kvp(
                patient_metadata, 'lizzie_fecal', 'Genotype', 'AOAH -/-, AhR R/R, CRF cre/+')

        elif cohort_key == 'Lizzie Fecal Ppar +/R, CRF cre/+, AOAH -/-':
            sample_keys = cohort_etl.filter_tornado_keys_patient_data_kvp(
                patient_metadata, 'lizzie_fecal', 'Genotype', 'Ppar +/R, CRF cre/+, AOAH -/-')

        elif cohort_key == 'Lizzie Fecal Ppar +/+, CRF cre/+':
            sample_keys = cohort_etl.filter_tornado_keys_patient_data_kvp(
                patient_metadata, 'lizzie_fecal', 'Genotype', 'Ppar +/+, CRF cre/+')
                
        elif cohort_key == 'Lizzie Patient 1':
            sample_keys = ['1-A1-WT1']

        return  sample_keys

class WenbinCecumSeedData(KlumppIC2SeedData):

    def get_biom_basename(self):
        basename = 'wenbin_cecum.biom'
        return basename

    def get_biom_file_box_url(self):
        return BIOM_BOX_URL_WENBIN_CECUM

    def get_cohort_configs(self):
        configs = [
        {
            'display_name_short': 'Wenbin Cecum Wildtype',
            'display_name_long': 'Wenbin Cecum Wild-type(B6)',
            'query': '((Lab=Wenbin) and (Sample Type=Cecum) and (Genotype=Wild-type(B6)))'
        },
        {
            'display_name_short': 'Wenbin Cecum AOAH -/-',
            'display_name_long': 'Wenbin Cecum AOAH -/-',
            'query': '((Lab=Wenbin) and (Sample Type=cecum) and (Genotype=AOAH -/-))'
        },
        {
            'display_name_short': 'Wenbin Cecum Patient 1',
            'display_name_long': 'Wenbin Cecum Patient 1',
            'query': '((Lab=Wenbin) and (Sample Type=cecum) and (ID=1-A4-B1))'
        }
        ]
        return configs

    def get_comparison_configs(self):
        configs = [
        {
            'comparison_key': 'wenbin_cecum_aoah',
            'display_name': 'Wenbin Cecum Wildtype vs. Wenbin Cecum AOAH -/-',
            'baseline_cohort_key': 'Wenbin Cecum Wildtype',
            'variant_cohort_key': 'Wenbin Cecum AOAH -/-',
            'patient_cohort_key': 'Wenbin Cecum Patient 1'
        }
        ]
        return configs

    def get_tornado_config(self):
        config = {
            'date_of_run': '2018-02-23T00:00:00Z',
            'display_name_short': 'wenbin_cecum'
        }
        return config

    def get_fst_results_cache_url(self, comparison_key): 
        url = None
        if comparison_key == 'wenbin_cecum_aoah':
            url = 'https://uofi.box.com/shared/static/646w6gm9hk71kp4paegp1ggvf1vvy8xt.csv'
        return url

    def get_tornado_sample_keys(self, cohort_key):
        patient_metadata = self.get_patient_metadata()
        
        if cohort_key == 'Wenbin Cecum Wildtype':
            sample_keys = cohort_etl.filter_tornado_keys_patient_data_kvp(
                patient_metadata, 'wenbin_cecum', 'Genotype', 'Wild-type(B6)')

        elif cohort_key == 'Wenbin Cecum AOAH -/-':
            sample_keys = cohort_etl.filter_tornado_keys_patient_data_kvp(
                patient_metadata, 'wenbin_cecum', 'Genotype', 'AOAH -/-')

        elif cohort_key == 'Wenbin Cecum Patient 1':
            sample_keys = ['1-C5-B1']

        return  sample_keys

class WenbinFecalSeedData(KlumppIC2SeedData):

    def get_biom_basename(self):
        basename = 'wenbin_fecal.biom'
        return basename

    def get_biom_file_box_url(self):
        return BIOM_BOX_URL_WENBIN_FECAL

    def get_cohort_configs(self):
        configs = [
        {
            'display_name_short': 'Wenbin Fecal Wildtype',
            'display_name_long': 'Wenbin Fecal Wild-type(B6)',
            'query': '((Lab=Wenbin) and (Sample Type=Fecal) and (Genotype=Wild-type(B6)))'
        },
        {
            'display_name_short': 'Wenbin Fecal AOAH -/-',
            'display_name_long': 'Wenbin Fecal AOAH -/-',
            'query': '((Lab=Wenbin) and (Sample Type=Fecal) and (Genotype=AOAH -/-))'
        },
        {
            'display_name_short': 'Wenbin Fecal Patient 1',
            'display_name_long': 'Wenbin Patient 1',
            'query': '((Lab=Wenbin) and (Sample Type=Fecal) and (ID=1-A4-B1))'
        }
        ]
        return configs

    def get_comparison_configs(self):
        configs = [
        {
            'comparison_key': 'wenbin_fecal_aoah',
            'display_name': 'Wenbin Fecal Wildtype vs. Wenbin Fecal AOAH -/-',
            'baseline_cohort_key': 'Wenbin Fecal Wildtype',
            'variant_cohort_key': 'Wenbin Fecal AOAH -/-',
            'patient_cohort_key': 'Wenbin Fecal Patient 1'
        }
        ]
        return configs

    def get_tornado_config(self):
        config = {
            'date_of_run': '2018-02-23T00:00:00Z',
            'display_name_short': 'wenbin_fecal'
        }
        return config

    def get_fst_results_cache_url(self, comparison_key): 
        url = None
        if comparison_key == 'wenbin_fecal_aoah':
            url = 'https://uofi.box.com/shared/static/u631o740sp4dzt9rcjd7zyzs6m6uv1o5.csv'
        return url

    def get_tornado_sample_keys(self, cohort_key):
        patient_metadata = self.get_patient_metadata()
        
        if cohort_key == 'Wenbin Fecal Wildtype':
            sample_keys = cohort_etl.filter_tornado_keys_patient_data_kvp(
                patient_metadata, 'wenbin_fecal', 'Genotype', 'Wild-type(B6)')

        elif cohort_key == 'Wenbin Fecal AOAH -/-':
            sample_keys = cohort_etl.filter_tornado_keys_patient_data_kvp(
                patient_metadata, 'wenbin_fecal', 'Genotype', 'AOAH -/-')

        elif cohort_key == 'Wenbin Fecal Patient 1':
            sample_keys = ['1-A4-B1']

        return  sample_keys

class WenbinCombinedSeedData(KlumppIC2SeedData):

    def get_biom_basename(self):
        basename = 'wenbin_combined.biom'
        return basename

    def get_biom_file_box_url(self):
        return BIOM_BOX_URL_WENBIN_COMBINED

    def get_cohort_configs(self):
        configs = [
        {
            'display_name_short': 'Wenbin (All) Wildtype',
            'display_name_long': 'Wenbin (All) Wild-type(B6)',
            'query': '((Lab=Wenbin) and (Genotype=Wild-type(B6)))'
        },
        {
            'display_name_short': 'Wenbin (All) AOAH -/-',
            'display_name_long': 'Wenbin (All) AOAH -/-',
            'query': '((Lab=Wenbin) and (Genotype=AOAH -/-))'
        },
        {
            'display_name_short': 'Wenbin Fecal Patient 1',
            'display_name_long': 'Wenbin Fecal Patient 1',
            'query': '((Lab=Wenbin) and (Sample Type=Fecal) and (ID=1-A4-B1))'
        }
        ]
        return configs

    def get_comparison_configs(self):
        configs = [
        {
            'comparison_key': 'wenbin_all_aoah',
            'display_name': 'Wenbin (All) Wildtype vs. Wenbin (All) AOAH -/-',
            'baseline_cohort_key': 'Wenbin (All) Wildtype',
            'variant_cohort_key': 'Wenbin (All) AOAH -/-',
            'patient_cohort_key': 'Wenbin Fecal Patient 1'
        }
        ]
        return configs

    def get_tornado_config(self):
        config = {
            'date_of_run': '2018-02-23T00:00:00Z',
            'display_name_short': 'wenbin_combined'
        }
        return config

    def get_fst_results_cache_url(self, comparison_key): 
        url = None
        if comparison_key == 'wenbin_all_aoah':
            url = 'https://uofi.box.com/shared/static/hx9ijkbzqxwl2n0vxlp74nu7d9xh3kpc.csv'
        return url

    def get_tornado_sample_keys(self, cohort_key):
        patient_metadata = self.get_patient_metadata()
        
        if cohort_key == 'Wenbin (All) Wildtype':
            sample_keys_1 = cohort_etl.filter_tornado_keys_patient_data_kvp(
                patient_metadata, 'wenbin_fecal', 'Genotype', 'Wild-type(B6)')
            sample_keys_2 = cohort_etl.filter_tornado_keys_patient_data_kvp(
                patient_metadata, 'wenbin_cecum', 'Genotype', 'Wild-type(B6)')
            sample_keys = sample_keys_1 + sample_keys_2

        elif cohort_key == 'Wenbin (All) AOAH -/-':
            sample_keys_1 = cohort_etl.filter_tornado_keys_patient_data_kvp(
                patient_metadata, 'wenbin_fecal', 'Genotype', 'AOAH -/-')
            sample_keys_2 = cohort_etl.filter_tornado_keys_patient_data_kvp(
                patient_metadata, 'wenbin_cecum', 'Genotype', 'AOAH -/-')
            sample_keys = sample_keys_1 + sample_keys_2

        elif cohort_key == 'Wenbin Fecal Patient 1':
            sample_keys = ['1-A4-B1']

        return  sample_keys

