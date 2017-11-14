import sys
import os
import json
import csv

import biom
from biom.table import Table as BiomTable

BIOM_FILE_NAME = '/home/pgroves/dat/mmbdb/PatientVis_Mar16/Paired/test_paired.biom'
METADATA_CSV_DIR_NAME = '/home/pgroves/dat/mmbdb/csv_exports/'

OUTPUT_DIR_NAME = '/home/pgroves/dat/mmbdb/meds_input/'
OUTPUT_DELIMETER = ','

TAXONOMY_LEVELS = ['kingdom', 'phyla', 'class', 'order', 'family', 'genus', 'species']

CRC_ADENOMA_BASE_NAME = 'Patient_Metadata_CRC_adenoma.csv'

SAMPLE_TO_PATIENT_BASE_NAME = 'Sample_to_Patient_Mappings.csv'

def main():
    if not os.path.exists(OUTPUT_DIR_NAME):
        os.makedirs(OUTPUT_DIR_NAME)
        
    bt = biom.load_table(BIOM_FILE_NAME)
    generate_otu_csv(bt)
    generate_sample_csv(bt)
    return

def generate_sample_csv(bt):
    sample_ids = bt.ids('sample')
    sample_csv_fn = OUTPUT_DIR_NAME + 'sample_metadata.csv'
    crc_adenoma_data = load_crc_adenoma()
    sample_mappings = load_mappings()
    sample_csv_header = ['sample_id', 'pi', 'tissue', 'organism', 'study_key', 
        'CRC_adenoma_Diagnosis1', 'CRC_adenoma_Diagnosis2', 
        'CRC_adenoma_Diagnosis3', 'CRC_adenoma_Diagnosis4']
    uniques_per_column = dict()
    for col_name in sample_csv_header[1:]:
        uniques_per_column[col_name] = set()
    with open(sample_csv_fn, 'wb') as csvfile:
        tbl_writer = csv.writer(csvfile, delimiter=OUTPUT_DELIMETER, lineterminator=os.linesep)
        tbl_writer.writerow(sample_csv_header)
        for sample_id in sample_ids:
            raw_metadata = bt.metadata(sample_id, 'sample')
            export_atts = dict()
            export_atts['sample_id'] = sample_id
            export_atts['pi'] = raw_metadata['PI']
            export_atts['tissue'] = raw_metadata['Tissue']
            export_atts['study_key'] = raw_metadata['Source_mapping_file']
            export_atts['organism'] = raw_metadata['Organism']
            if export_atts['study_key'] == 'CRC_adenoma':
                sample_mapping = sample_mappings[sample_id]
                study_sample_id = sample_mapping['study_sample_id']
                assert(sample_mapping['study_key'] == 'CRC_adenoma')
                crc_metadata = crc_adenoma_data[study_sample_id]
                export_atts['CRC_adenoma_Diagnosis1'] = crc_metadata['Diagnosis1']
                export_atts['CRC_adenoma_Diagnosis2'] = crc_metadata['Diagnosis2']
                export_atts['CRC_adenoma_Diagnosis3'] = crc_metadata['Diagnosis3']
                export_atts['CRC_adenoma_Diagnosis4'] = crc_metadata['Diagnosis4']
            else:
                export_atts['CRC_adenoma_Diagnosis1'] = 'NA'
                export_atts['CRC_adenoma_Diagnosis2'] = 'NA'
                export_atts['CRC_adenoma_Diagnosis3'] = 'NA'
                export_atts['CRC_adenoma_Diagnosis4'] = 'NA'

            for col_name in sample_csv_header[1:]:
                uniques_per_column[col_name].add(export_atts[col_name])

            export_row = list()
            for col_name in sample_csv_header:
                export_row.append(export_atts[col_name])

            tbl_writer.writerow(export_row)

    print("uniques per non-sample_id column")
    for col_name in uniques_per_column:
        print('  ' + col_name + ': ' + str(list(uniques_per_column[col_name])) + '\n')
    return

def load_crc_adenoma():
    """
    returns a dict of (sample_id ->  (dict of attributes in csv file))
    """
    crc_data_fn = METADATA_CSV_DIR_NAME + CRC_ADENOMA_BASE_NAME 
    #the 'filename' attribute is the one in the metadata that is also in
    #the mappings file. SampleId seems to only be used locally, even though
    #it's globally unique
    crc_data = csv_file_to_nested_dict(crc_data_fn, 'FileName') 
    return crc_data
    

def load_mappings():
    """
    returns a dict of geno sample_id -> dict of (study_key, study_sample_id)
    """
    fn = METADATA_CSV_DIR_NAME + SAMPLE_TO_PATIENT_BASE_NAME 
    raw_mappings = csv_file_to_nested_dict(fn, 'SampleID')
    clean_mappings = dict()
    for sample_id in raw_mappings:
        raw_atts = raw_mappings[sample_id]
        clean_atts = dict()
        clean_atts['sample_id'] = sample_id
        clean_atts['study_key'] = raw_atts['Source_mapping_file']
        clean_atts['study_sample_id'] = raw_atts['FileName']
        clean_mappings[sample_id] = clean_atts
    return clean_mappings

def generate_otu_csv(bt):
    otu_id_numbers = (sorted(map(int, (bt.ids('observation')))))
    otu_csv_fn = OUTPUT_DIR_NAME + 'OTU_taxonomies.csv'
    otu_csv_header= ['OTU_Name'] + TAXONOMY_LEVELS
    with open(otu_csv_fn, 'wb') as csvfile:
        tbl_writer = csv.writer(csvfile, delimiter=OUTPUT_DELIMETER, lineterminator=os.linesep)
        tbl_writer.writerow(otu_csv_header)

        for i in otu_id_numbers:
            observation_id = str(i)
            export_name = 'OTU-' + str(i)
            raw_metadata = bt.metadata(observation_id, 'observation')
            #print('original otu metadata:')
            #print_as_json(raw_taxonomy)
            taxonomy_atts = parse_taxonomy(raw_metadata)

            export_row = list()
            export_row.append(export_name)
            for tax_level in TAXONOMY_LEVELS:
                tax_val = taxonomy_atts[tax_level]
                export_row.append(tax_val)

            #print('csv row: ' + str(export_row))
            #print_as_json(bt.metadata(observation_id, 'observation'))
            tbl_writer.writerow(export_row)
    return

def print_as_json(x):
    print(json.dumps(x, indent=4))

def csv_file_to_nested_dict(filename, primary_key_col):
    """
    assumes the first line of the csv is column names. loads each line
    into a dict of kvps where key is column name and value is the value 
    in the cell.

    Puts all of these kvp dicts into one top level dict, where the key
    is the value of the 'primary_key_col' and the value is the kvp dict.
    """
    nested_dict = dict()
    with open(filename) as csvfile:
        reader = csv.DictReader(csvfile)
        for row_dict in reader:
            primary_key = row_dict[primary_key_col]
            nested_dict[primary_key] = row_dict
    print('loaded csv file to nested dict: ' + filename)
    print_as_json(nested_dict)
    return nested_dict

def parse_taxonomy(otu_metadata_from_biom_file):
    taxa_atts = dict()
    observed_vals = otu_metadata_from_biom_file['taxonomy']
    for i in range(len(TAXONOMY_LEVELS)):
        level = TAXONOMY_LEVELS[i]
        raw_taxa = observed_vals[i] # should be like 'k__Bacteria' or 'unclassified'
        if raw_taxa == 'unclassified':
            taxa_atts[level] = 'unclassified'
            #if not level == 'species':
            #    print('saw unclassifed at level: ' + level)
        else:
            #first characters should match
            assert(level[0] == raw_taxa[0])
            taxa = raw_taxa[3:]
            taxa_atts[level] = taxa
    #print('parsed taxonomy to: ')
    #print_as_json(taxa_atts)
    return taxa_atts

if __name__ == '__main__':
    #load_biom(sys.argv[1:])
    main()

