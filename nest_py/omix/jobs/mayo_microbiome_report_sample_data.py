"""
Seed job data for Mayo microbiome report sample data.
"""
import os

import pandas as pd
from biom.table import Table as BiomTable

import nest_py.core.jobs.box_downloads as box_downloads
from nest_py.omix.jobs.seed_data import SeedFlavorData

TAXA_URL = 'https://uofi.box.com/shared/static/49gifn6o35jvajcsrmghrjy5ddqab170.csv'

OTUS_URL = 'https://uofi.box.com/shared/static/0577h5zmiijfh0rhx4khs7mfh4hcg5y4.csv'

DEMOGRAPHIC_COLUMNS = ['Age', 'Sex', 'Study'] # all others in OTUS_URL are abundances

TAX_LEVELS = [
    {'name': 'kingdom', 'silva_index': 0, 'suffix': '_ki', 'prefix': 'k__'},
    {'name': 'phylum', 'silva_index': 1, 'suffix': '_ph', 'prefix': 'p__'},
    {'name': 'class', 'silva_index': 2, 'suffix': '_cl', 'prefix': 'c__'},
    {'name': 'order', 'silva_index': 3, 'suffix': '_or', 'prefix': 'o__'},
    {'name': 'family', 'silva_index': 4, 'suffix': '_fa', 'prefix': 'f__'},
    {'name': 'genus', 'silva_index': 5, 'suffix': '_ge', 'prefix': 'g__'},
]

class MayoMicrobiomeReportSampleSeedData(SeedFlavorData):

    def __init__(self, data_dir, file_owner):
        self.data_dir = data_dir
        self.file_owner = file_owner
        self.biom_table = None
        self.sample_metadata_df = None
        super(MayoMicrobiomeReportSampleSeedData, self).__init__()

    def get_username(self):
        return 'mayo-report'

    def get_userpass(self):
        return 'MicrobiomeReport2019'

    def get_biom_table(self):
        if self.biom_table is None:
            self.load_biom_table()
        return self.biom_table

    def get_cohort_configs(self):
        return cohort_configs()

    def get_comparison_configs(self):
        return comparison_configs()

    def get_tornado_config(self):
        return {
            'date_of_run': 'unknown',
            'display_name_short': 'mayo_report'
        }

    def get_fst_results_cache_url(self, comparison_key):
        return {
            'report_male_young': \
                'https://uofi.box.com/shared/static/8a4ddl4c6by9hv2x44716gmjt5iuu0dt.csv',
            'report_male_mid': \
                'https://uofi.box.com/shared/static/tlrq2yypa4v5fofxei5vhl20iboemn73.csv',
            'report_male_old': \
                'https://uofi.box.com/shared/static/9l0drm7uzqu5a9k4v6qx1t9d8i9xyx98.csv',
            'report_female_young': \
                'https://uofi.box.com/shared/static/govfl3wy8blhsdgfda5zi995aoiwh6hk.csv',
            'report_female_mid': \
                'https://uofi.box.com/shared/static/94b6s1ggqfqez7f8n5qos9kuqmo79v0n.csv',
            'report_female_old': \
                'https://uofi.box.com/shared/static/d35f0798hmaala2cp8brmizo1ldan9i2.csv'
        }[comparison_key]

    def get_tornado_sample_keys(self, cohort_key):
        if self.sample_metadata_df is None:
            self.load_biom_table()
        mdf = self.sample_metadata_df # fewer characters just for this method

        sample_keys = None

        if cohort_key == 'Male/Young':
            sample_keys = \
                mdf[(mdf['Sex'] == 'M') & (mdf['Age'] < 35)].index.tolist()
        elif cohort_key == 'Male/Mid':
            sample_keys = \
                mdf[(mdf['Sex'] == 'M') & (mdf['Age'] >= 35) & (mdf['Age'] < 55)].index.tolist()
        elif cohort_key == 'Male/Old':
            sample_keys = \
                mdf[(mdf['Sex'] == 'M') & (mdf['Age'] > 55)].index.tolist()
        elif cohort_key == 'Female/Young':
            sample_keys = \
                mdf[(mdf['Sex'] == 'F') & (mdf['Age'] < 35)].index.tolist()
        elif cohort_key == 'Female/Mid':
            sample_keys = \
                mdf[(mdf['Sex'] == 'F') & (mdf['Age'] >= 35) & (mdf['Age'] < 55)].index.tolist()
        elif cohort_key == 'Female/Old':
            sample_keys = \
                mdf[(mdf['Sex'] == 'F') & (mdf['Age'] > 55)].index.tolist()
        elif cohort_key == 'Not Male/Young':
            sample_keys = \
                mdf[(mdf['Sex'] != 'M') | (mdf['Age'] >= 35)].index.tolist()
        elif cohort_key == 'Not Male/Mid':
            sample_keys = \
                mdf[(mdf['Sex'] != 'M') | (mdf['Age'] < 35) | (mdf['Age'] >= 55)].index.tolist()
        elif cohort_key == 'Not Male/Old':
            sample_keys = \
                mdf[(mdf['Sex'] != 'M') | (mdf['Age'] <= 55)].index.tolist()
        elif cohort_key == 'Not Female/Young':
            sample_keys = \
                mdf[(mdf['Sex'] != 'F') | (mdf['Age'] >= 35)].index.tolist()
        elif cohort_key == 'Not Female/Mid':
            sample_keys = \
                mdf[(mdf['Sex'] != 'F') | (mdf['Age'] < 35) | (mdf['Age'] >= 55)].index.tolist()
        elif cohort_key == 'Not Female/Old':
            sample_keys = \
                mdf[(mdf['Sex'] != 'F') | (mdf['Age'] <= 55)].index.tolist()
        elif cohort_key == '1 Male/Young':
            sample_keys = ['SAMEA4431963']
        elif cohort_key == '1 Male/Mid':
            sample_keys = ['SAMEA2581957']
        elif cohort_key == '1 Male/Old':
            sample_keys = ['SAMEA3136674']
        elif cohort_key == '1 Female/Young':
            sample_keys = ['SAMN03283277']
        elif cohort_key == '1 Female/Mid':
            sample_keys = ['SAMEA2581954']
        elif cohort_key == '1 Female/Old':
            sample_keys = ['SAMEA3136642']
        else:
            raise ValueError('Unknown cohort_key ' + cohort_key)

        return sample_keys

    def load_biom_table(self):

        otus_path = os.path.join(self.data_dir, 'mayo_report', 'WT.csv')
        taxa_path = os.path.join(self.data_dir, 'mayo_report', 'taxonomy.csv')

        box_downloads.download_from_box_no_auth(\
            OTUS_URL, otus_path, file_owner=self.file_owner)

        box_downloads.download_from_box_no_auth(\
            TAXA_URL, taxa_path, file_owner=self.file_owner)

        # note: we have species, not OTUs, but we'll pretend
        # sample_df has one row for each sample and columns for demographic and
        # abundance data
        sample_df = pd.read_csv(otus_path, sep=',', index_col=0, header=0,\
            mangle_dupe_cols=False, error_bad_lines=True)

        # taxa_df has one row for each "otu" and columns for taxonomic data
        taxa_df = pd.read_csv(taxa_path, sep=',', index_col=0, header=0,\
            mangle_dupe_cols=False, error_bad_lines=True)

        sample_ids = sample_df.index.tolist()

        species_labels = taxa_df.index.tolist()
        # confirm that "otus" appear in the same order in both files, so we
        # don't have to reorder anything later
        assert species_labels == [col for col in sample_df.columns \
            if col not in DEMOGRAPHIC_COLUMNS]

        # need "otus" as rows, samples as columns
        observations_nary = sample_df[species_labels].values.transpose()

        otu_metadata = construct_otu_metadata(taxa_df)

        # sample_metadata needs to be a list with one element per sample
        # each sample's element is a dict w/ demographic data and sample_id
        self.sample_metadata_df = sample_df[DEMOGRAPHIC_COLUMNS].copy()
        self.sample_metadata_df['sample_id'] = self.sample_metadata_df.index
        sample_metadata = self.sample_metadata_df.to_dict('records')

        # otu_number_ids needs to be a list of strings
        otu_number_ids = taxa_df['otu'].apply(str).tolist()

        self.biom_table = BiomTable(observations_nary, otu_number_ids, \
            sample_ids, otu_metadata, sample_metadata, table_id='MayoReport')

def construct_otu_metadata(taxa_df):
    # need to return a list with one element per "otu"
    # each otu's element is a dict with one key, "taxonomy"
    # the dict's one value is a list of taxonomic labels, one per level

    def format_level(otu_s, level_name, level_prefix):
        # taxonomic labels get a level-specific prefix unless they're
        # "unclassified"
        return_val = otu_s[level_name]
        if return_val != 'unclassified':
            return_val = level_prefix + return_val
        return return_val

    def get_taxonomy(otu_s):
        # otu_s is a pd.Series indexed by taxonomic level names from kingdom
        # down to genus
        taxa = [format_level(otu_s, level['name'], level['prefix']) for \
            level in TAX_LEVELS]
        # the name of otu_s is the species name, formatted as Jae provided
        taxa.append(otu_s.name)
        return {'taxonomy': taxa}

    return taxa_df.apply(get_taxonomy, axis=1, reduce=True).tolist()

# internal caller only
def cohort_configs():
    configs = [
        {
            'display_name_short': 'Male/Young',
            'display_name_long': 'Male under 35',
            'query': '(Sex=M) and (Age < 35)'
        },
        {
            'display_name_short': 'Male/Mid',
            'display_name_long': 'Male between 35 and 55',
            'query': '(Sex=M) and (Age >= 35) and (Age < 55)'
        },
        {
            'display_name_short': 'Male/Old',
            'display_name_long': 'Male over 55',
            'query': '(Sex=M) and (Age >= 55)'
        },
        {
            'display_name_short': 'Female/Young',
            'display_name_long': 'Female under 35',
            'query': '(Sex=F) and (Age < 35)'
        },
        {
            'display_name_short': 'Female/Mid',
            'display_name_long': 'Female between 35 and 55',
            'query': '(Sex=F) and (Age >= 35) and (Age < 55)'
        },
        {
            'display_name_short': 'Female/Old',
            'display_name_long': 'Female over 55',
            'query': '(Sex=F) and (Age >= 55)'
        },
        {
            'display_name_short': 'Not Male/Young',
            'display_name_long': 'Not male under 35',
            'query': '(Sex!=M) or (Age >= 35)'
        },
        {
            'display_name_short': 'Not Male/Mid',
            'display_name_long': 'Not male between 35 and 55',
            'query': '(Sex!=M) or (Age < 35) or (Age >= 55)'
        },
        {
            'display_name_short': 'Not Male/Old',
            'display_name_long': 'Not male over 55',
            'query': '(Sex!=M) or (Age < 55)'
        },
        {
            'display_name_short': 'Not Female/Young',
            'display_name_long': 'Not female under 35',
            'query': '(Sex!=F) or (Age >= 35)'
        },
        {
            'display_name_short': 'Not Female/Mid',
            'display_name_long': 'Not female between 35 and 55',
            'query': '(Sex!=F) or (Age < 35) or (Age >= 55)'
        },
        {
            'display_name_short': 'Not Female/Old',
            'display_name_long': 'Not female over 55',
            'query': '(Sex!=F) or (Age < 55)'
        },
        {
            'display_name_short': '1 Male/Young',
            'display_name_long': '1 Male under 35',
            'query': '(sample_id=SAMEA4431963)'
        },
        {
            'display_name_short': '1 Male/Mid',
            'display_name_long': '1 Male between 35 and 55',
            'query': '(sample_id=SAMEA2581957)'
        },
        {
            'display_name_short': '1 Male/Old',
            'display_name_long': '1 Male over 55',
            'query': '(sample_id=SAMEA3136674)'
        },
        {
            'display_name_short': '1 Female/Young',
            'display_name_long': '1 Female under 35',
            'query': '(sample_id=SAMN03283277)'
        },
        {
            'display_name_short': '1 Female/Mid',
            'display_name_long': '1 Female between 35 and 55',
            'query': '(sample_id=SAMEA2581954)'
        },
        {
            'display_name_short': '1 Female/Old',
            'display_name_long': '1 Female over 55',
            'query': '(sample_id=SAMEA3136642)'
        }
    ]
    return configs

# internal caller only
def comparison_configs():
    configs = [
        {
            'comparison_key': 'report_male_young',
            'display_name': 'Report: Male/Young vs. Others',
            'baseline_cohort_key': 'Not Male/Young',
            'variant_cohort_key': 'Male/Young',
            'patient_cohort_key': '1 Male/Young'
        },
        {
            'comparison_key': 'report_male_mid',
            'display_name': 'Report: Male/Mid vs. Others',
            'baseline_cohort_key': 'Not Male/Mid',
            'variant_cohort_key': 'Male/Mid',
            'patient_cohort_key': '1 Male/Mid'
        },
        {
            'comparison_key': 'report_male_old',
            'display_name': 'Report: Male/Old vs. Others',
            'baseline_cohort_key': 'Not Male/Old',
            'variant_cohort_key': 'Male/Old',
            'patient_cohort_key': '1 Male/Old'
        },
        {
            'comparison_key': 'report_female_young',
            'display_name': 'Report: Female/Young vs. Others',
            'baseline_cohort_key': 'Not Female/Young',
            'variant_cohort_key': 'Female/Young',
            'patient_cohort_key': '1 Female/Young'
        },
        {
            'comparison_key': 'report_female_mid',
            'display_name': 'Report: Female/Mid vs. Others',
            'baseline_cohort_key': 'Not Female/Mid',
            'variant_cohort_key': 'Female/Mid',
            'patient_cohort_key': '1 Female/Mid'
        },
        {
            'comparison_key': 'report_female_old',
            'display_name': 'Report: Female/Old vs. Others',
            'baseline_cohort_key': 'Not Female/Old',
            'variant_cohort_key': 'Female/Old',
            'patient_cohort_key': '1 Female/Old'
        }
    ]
    return configs
