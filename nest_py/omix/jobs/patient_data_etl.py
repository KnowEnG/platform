import csv

import nest_py.core.jobs.jobs_logger as logger
import nest_py.ops.container_users as container_users
import nest_py.core.jobs.box_downloads as box_downloads
import nest_py.core.jobs.file_utils as file_utils

MAPPINGS_FILE_URL = 'https://uofi.box.com/shared/static/36okh31btcg868pjg9p2jithufa9f4a9.csv'
MAPPINGS_FILE_DEST = 'PatientVis_Mar16/csv_exports/Sample_to_Patient_Mappings.csv'

#the keys are study_key values used elsewhere. in the sample mappings file, it's the Source_mapping_file column
PATIENT_DATA_URLS= {
    'Cdiff': {
        'url':'https://uofi.box.com/shared/static/kqi9xxd9o9dy52vrwxo1o9zpku2i6f4a.csv',
        'dest_filename': 'PatientVis_Mar16/csv_exports/Patient_Metadata_Cdiff_Pardi.csv'
    },
    'CRC_adenoma': {
        'url':'https://uofi.box.com/shared/static/lnoguy9ot6zt41017kh1pr4kr22lyoyc.csv',
        'dest_filename': 'PatientVis_Mar16/csv_exports/Patient_Metadata_CRC_OutsideResearch.csv'
    },
    'Lambert_Nathaniel': {
        'url':'https://uofi.box.com/shared/static/j8prmzhr4tzqaoayrnajmdt9lpgygizo.csv',
        'dest_filename': 'PatientVis_Mar16/csv_exports/Patient_Metadata_Lambert.csv'
    },
    'Taneja_RA_Normal_Relatives': {
        'url':'https://uofi.box.com/shared/static/p895pe05dghl3yscax4bd6oby4n87sau.csv',
        'dest_filename': 'PatientVis_Mar16/csv_exports/Patient_Metadata_Taneja_RA_Normal_Relatives.csv'

    }
}

STUDY_METADATA =  {
    'Cdiff': {
        'papers': """7.07 Differences in the fecal microbiome and outcomes in patients with Clostridium difficile infection""",
        'irb_numbers':"""12-000554  12-005805 12-007176""",
        'principal_investigators':"""Pardi, Darrell, M.D.""",

        'inclusion_criteria_description':
            """12-000554 No specific inclusion/exclusion criteria specified in the protocol, just states patients with C. difficile infection.
        12-005805 - Inclusion: Age 18 or older. Diagnosis of Microscopic colitis at Mayo Clinic. 
        12-007176 Inclusion - Age 18 and over; undergoing stool testing for diarrhea and test negative for Clostridium difficile """,

        'exclusion_criteria_description':
            """12-000554 No specific inclusion/exclusion criteria specified in the protocol, just states patients with C. difficile infection. 
        12-005805 - No exclusions. 
        12-007176 Exclusion - Individuals who do not comprehend or speak English ( i.e., participants must be able to understand and  give consent without the assistance of an interpreter).
        -Age 17 and younger
        -Individuals regarded as belonging to a vulnerable population ( prisoners, children, etc )
        """
    },
    'CRC_adenoma': None,
    'Lambert_Nathaniel': None,
    'Taneja_RA_Normal_Relatives': None
}

      
def load_all_metadata(destination_data_dir):
    """
    destination_data_dir: string of directory name to download data to

    returns a nested dictionary of
    <study_key> -> {
        'metatdata': {
            'papers': list of string,
            'irb_numbers': list of string,
            'principl_investigators': list of string,
            'inclusion_criteria_description': string,
            'exclusion_criteria_description': string,
        },
        'attributes': [
        ],
        'patients': {
            <tornado_sample_key> : {
                <study_specific_att1>: value,
                <study_specific_att2>: value,
                etc
            }

        }
    }
    where 'tornado_sample_key' is the sample identifier in the tornado output
    biomTable
    """ 
    download_all_box_data(destination_data_dir)
    data = dict()
    data['Cdiff'] = load_cdiff_data(destination_data_dir)
    data['CRC_adenoma'] = load_crc_adenoma_data(destination_data_dir)
    data['Lambert_Nathaniel'] = load_lambert_vaccine_data(destination_data_dir)
    data['Taneja_RA_Normal_Relatives'] = load_taneja_data(destination_data_dir)
    #logger.pretty_print_jdata(data)
    return data

def load_taneja_data(data_dir):
    data = init_study_data()
    study_key = 'Taneja_RA_Normal_Relatives'
    data['metadata'] = STUDY_METADATA[study_key]
    csv_fn = data_dir + PATIENT_DATA_URLS[study_key]['dest_filename']
    data['attributes'] = file_utils.csv_file_column_names(csv_fn)

    sample_mappings = load_mappings(data_dir)
    sample_key_col = 'SampleID'
    raw_patients_data = file_utils.csv_file_to_nested_dict(csv_fn, sample_key_col)

    for raw_sample_key in raw_patients_data:
        raw_patient_data = raw_patients_data[raw_sample_key]
        #the spreadsheet has sample_ids that start with MWR and HLTY that do
        #not have entries in the sample_mappings and therefore(?) dont't have
        #any OTU data in the biom file to associate with.
        #the rows that have a SampleId that starts with 'V' are the good ones
        if raw_sample_key[0] == 'V':
            study_sample_key =  's' + (str(raw_sample_key)).lower()
            tornado_sample_key = sample_mappings[study_key][study_sample_key]

            patient_data = dict()
            patient_data['study_sample_key'] = study_sample_key
            patient_data['tornado_sample_key'] = tornado_sample_key

            relation_id = raw_patient_data['Relation']
            if relation_id == raw_sample_key:
                patient_data['is_patient'] = True
                patient_data['is_family'] = False
            else:
                patient_data['is_patient'] = False
                patient_data['is_family'] = True 

            data['patients'][tornado_sample_key] = patient_data
    return data


def load_lambert_vaccine_data(data_dir):
    data = init_study_data()
    study_key = 'Lambert_Nathaniel'
    data['metadata'] = STUDY_METADATA[study_key]
    csv_fn = data_dir + PATIENT_DATA_URLS[study_key]['dest_filename']
    data['attributes'] = file_utils.csv_file_column_names(csv_fn)

    sample_mappings = load_mappings(data_dir)
    sample_key_col = 'SampleID'
    raw_patients_data = file_utils.csv_file_to_nested_dict(csv_fn, sample_key_col)

    for raw_sample_key in raw_patients_data:
        study_sample_key =  's' + (str(raw_sample_key)).lower()
        raw_patient_data = raw_patients_data[raw_sample_key]
        tornado_sample_key = sample_mappings[study_key][study_sample_key]

        patient_data = dict()
        patient_data['study_sample_key'] = study_sample_key
        patient_data['tornado_sample_key'] = tornado_sample_key

        days_since_vaccine_slug = raw_patient_data['Day'].strip()
        patient_data['days_since_vaccine'] = days_since_vaccine_slug
        data['patients'][tornado_sample_key] = patient_data
    return data


def load_cdiff_data(data_dir):
    data = init_study_data()
    study_key = 'Cdiff'
    data['metadata'] = STUDY_METADATA[study_key]
    csv_fn = data_dir + PATIENT_DATA_URLS[study_key]['dest_filename']
    data['attributes'] = file_utils.csv_file_column_names(csv_fn)

    sample_mappings = load_mappings(data_dir)
    sample_key_col = 'SampleID'
    raw_patients_data = file_utils.csv_file_to_nested_dict(csv_fn, sample_key_col)

    for raw_sample_key in raw_patients_data:
        study_sample_key = 'ssx' + (str(raw_sample_key)).lower()
        raw_patient_data = raw_patients_data[raw_sample_key]
        tornado_sample_key = sample_mappings[study_key][study_sample_key]

        patient_data = dict()
        patient_data['study_sample_key'] = study_sample_key
        patient_data['tornado_sample_key'] = tornado_sample_key

        cdiff_slug = raw_patient_data['Description'].strip()
        if cdiff_slug == 'Normal':
            cdiff_clean = 'normal'
        elif cdiff_slug in ['C-diff +', 'C-diff+']:
            cdiff_clean = 'positive'
        elif cdiff_slug in ['C-diff -', 'C-diff-'] :
            cdiff_clean = 'negative'
        else:
            raise Exception("Unknown cdiff Description: " + str(cdiff_slug))
        patient_data['cdiff_level'] = cdiff_clean
        
        data['patients'][tornado_sample_key] = patient_data
    return data

def load_crc_adenoma_data(data_dir):
    data = init_study_data()
    study_key = 'CRC_adenoma'
    data['metadata'] = STUDY_METADATA[study_key]
    csv_fn = data_dir + PATIENT_DATA_URLS[study_key]['dest_filename']
    data['attributes'] = file_utils.csv_file_column_names(csv_fn)

    sample_mappings = load_mappings(data_dir)
    sample_key_col = 'SampleID'
    raw_patients_data = file_utils.csv_file_to_nested_dict(csv_fn, sample_key_col)

    for raw_sample_key in raw_patients_data:
        study_sample_key = 's' + (str(raw_sample_key)).lower()
        raw_patient_data = raw_patients_data[raw_sample_key]
        tornado_sample_key = sample_mappings[study_key][study_sample_key]

        patient_data = dict()
        patient_data['study_sample_key'] = study_sample_key
        patient_data['tornado_sample_key'] = tornado_sample_key

        diagnosis = raw_patient_data['Diagnosis'].strip()
        if diagnosis in ['cancer', 'adenoma', 'normal']:
            patient_data['Diagnosis'] = diagnosis
        else:
            raise Exception("Unexpected value in CRC Diagnosis Column: " + str(diagnosis))

        polyps = raw_patient_data['POLYP.1=Y']
        if polyps in ['1', '0']:
            patient_data['POLYP.1=Y'] = polyps
        else:
            raise Exception("Unexpected value in CRC POLYP.1=Y Column: " + str(polyps))

        data['patients'][tornado_sample_key] = patient_data
    return data


def download_all_box_data(data_dir):
    """
    ensures that all the data on Box that we need is downloaded to
    it's correct file locations
    """

    file_owner = container_users.make_host_user_container_user()
    for study_key in PATIENT_DATA_URLS:
        box_url = PATIENT_DATA_URLS[study_key]['url']
        abs_filename = data_dir + PATIENT_DATA_URLS[study_key]['dest_filename']
        box_downloads.download_from_box_no_auth(box_url, abs_filename, 
            file_owner=file_owner, force=False)

    box_url = MAPPINGS_FILE_URL
    abs_filename =  data_dir + MAPPINGS_FILE_DEST
    box_downloads.download_from_box_no_auth(box_url, abs_filename, 
        file_owner=file_owner, force=False)
    return

def load_mappings(data_dir):
    """
    nested dict of {study_key: {study_sample_key: tornado_sample_key}}
    """
    fn = data_dir + MAPPINGS_FILE_DEST
    raw_mappings = file_utils.csv_file_to_nested_dict(fn, 'SampleID')
    clean_mappings = dict()
    for raw_sample_key in raw_mappings:
        raw_atts = raw_mappings[raw_sample_key]
        study_sample_key = raw_sample_key.lower()
        #tornado_sample_key = raw_atts['FileName']
        tornado_sample_key = raw_sample_key
        study_key = raw_atts['Source_mapping_file']
        if not study_key in clean_mappings:
            clean_mappings[study_key] = dict()
        clean_mappings[study_key][study_sample_key] = tornado_sample_key

    return clean_mappings

def init_study_data():
    """
    make an empty dict for a study
    """
    study_data = dict()
    study_data['metadata'] = dict()
    study_data['attributes'] = list()
    study_data['patients'] = dict()
    return study_data




