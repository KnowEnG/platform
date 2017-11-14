"""
This module defines a class for running knoweng's spreadsheet preprocess jobs.
"""
import csv
from enum import Enum
import logging
import os
from time import sleep

import yaml

from nest_py.knoweng.jobs.chronos_job import ChronosJob
import nest_py.knoweng.data_types.files as files

PipelineType = Enum('PipelineType', \
    'GENE_PRIORITIZATION GENE_SET_CHARACTERIZATION SAMPLE_CLUSTERING SPREADSHEET_VISUALIZATION')
CorrelationMeasure = Enum('CorrelationMeasure', 'T_TEST PEARSON')

# this is the logger configured for nest_jobs. TODO clean up logging everywhere
LOGGER = logging.getLogger('rq.worker')

class DataCleanupJob(ChronosJob):
    """Subclass of ChronosJob that handles data cleanup jobs."""
    def __init__(self, user_id, job_id, userfiles_dir, timeout, cloud,
                 species_id, input_spreadsheet_file_dto,
                 input_phenotype_file_dto, gg_network_name_full_path,
                 run_directory_relative_path, pipeline_type,
                 correlation_measure):
        """Initializes self.

        Args:
            user_id (NestId): The user id associated with the job.
            job_id (Nestid): The job id associated with the job.
            userfiles_dir (str): The base directory containing all files for
                all users.
            timeout (int): The maximum execution time in seconds.
            cloud (str): The cloud name, which must appear as a key in
                nest_py.knoweng.jobs.ChronosJob.cloud_path_dict.
            species_id (str): The species_id to use when looking up gene names.
            input_spreadsheet_file_dto(FileDTO):
                The spreadsheet file's database record.
            input_phenotype_file_dto(FileDTO):
                The phenotype file's database record,
                or None if there is no phenotype file.
            gg_network_name_full_path (str): The path to the gene-gene network
                edge file. Only used for sample clustering with network
                smoothing.
            run_directory_relative_path (str): The relative path from
                userfiles_dir to the run directory for the data cleanup job.
                Must already exist.
            pipeline_type (PipelineType): The pipeline type.
            correlation_measure (CorrelationMeasure): If pipeline_type is
                GENE_PRIORITIZATION, then the correlation measure, else None.

        Returns:
            None: None.

        """
        self.input_spreadsheet_file_dto = input_spreadsheet_file_dto
        self.input_phenotype_file_dto = input_phenotype_file_dto
        self.run_directory_relative_path = run_directory_relative_path

        input_spreadsheet_relative_path = \
            get_relative_path_to_uploaded_file(self.input_spreadsheet_file_dto)

        input_phenotype_relative_path = None
        if input_phenotype_file_dto is not None:
            input_phenotype_relative_path = \
                get_relative_path_to_uploaded_file(input_phenotype_file_dto)

        # create yaml file
        redis_params = ChronosJob.cloud_redis_dict[cloud]
        run_data = {
            'spreadsheet_name_full_path': input_spreadsheet_relative_path,
            'results_directory': './',
            'taxonid': species_id,
            'source_hint': '',
            'redis_credential': {
                'host': redis_params['host'],
                'port': redis_params['port'],
                'password': redis_params['password']
            }
        }
        if input_phenotype_relative_path is not None:
            run_data['phenotype_name_full_path'] = input_phenotype_relative_path
        if gg_network_name_full_path is not None:
            run_data['gg_network_name_full_path'] = gg_network_name_full_path
        if pipeline_type is PipelineType.GENE_PRIORITIZATION:
            self.pipeline_type = 'gene_prioritization_pipeline'
            if correlation_measure is CorrelationMeasure.T_TEST:
                run_data['correlation_measure'] = 't_test'
            elif correlation_measure is CorrelationMeasure.PEARSON:
                run_data['correlation_measure'] = 'pearson'
            else:
                # TODO report error
                pass
        elif pipeline_type is PipelineType.GENE_SET_CHARACTERIZATION:
            self.pipeline_type = 'geneset_characterization_pipeline'
        # TODO: Update this if/when a new Docker image is created for SSV
        elif pipeline_type is PipelineType.SAMPLE_CLUSTERING or pipeline_type is PipelineType.SPREADSHEET_VISUALIZATION:
            self.pipeline_type = 'samples_clustering_pipeline'
        else:
            # TODO report error
            pass
        run_data['pipeline_type'] = self.pipeline_type

        yml_path = os.path.join(\
            userfiles_dir, run_directory_relative_path, 'run_cleanup.yml')
        with open(yml_path, 'wb') as outfile:
            yaml.safe_dump(run_data, outfile, default_flow_style=False)

        cleanup_job_name = 'nest_data_cleanup_' + job_id.to_slug()
        super(DataCleanupJob, self).__init__(\
            user_id, job_id, userfiles_dir, run_directory_relative_path, \
            cleanup_job_name, timeout, cloud,
            'knowengdev/data_cleanup_pipeline:07_26_2017', 1, 5000)

    def get_command(self):
        """Returns the docker command for data_cleanup."""
        cd_path = os.path.join(ChronosJob.cloud_path_dict[self.cloud],\
            'userfiles', self.run_directory_relative_path)
        return 'date && cd ' + cd_path + \
            ' && python3 /home/src/data_cleanup.py ' + \
            ' -run_directory ./' + \
            ' -run_file run_cleanup.yml' + \
            ' && date;'

    def is_ready(self):
        """Returns True always."""
        return True

    def is_failed(self):
        """Returns True if the pipeline reported an error."""
        return self.get_error_message() is not None

    def get_error_message(self):
        """Returns the error messages reported by the pipeline, if any."""
        log_file_path = os.path.join(self.userfiles_dir, \
            self.run_directory_relative_path, \
            'log_' + self.pipeline_type + '.yml')
        return_val = None
        if os.path.isfile(log_file_path):
            with open(log_file_path, 'r') as log:
                log_dict = yaml.safe_load(log)
                if 'FAIL' in log_dict:
                    prefix = 'ERROR: '
                    messages = [msg.replace(prefix, '') for msg \
                        in log_dict['FAIL'] if msg.startswith(prefix)]
                    if messages:
                        return_val = ' '.join(messages)
                    else:
                        return_val = 'Unknown input error.'
        return return_val

    def is_done(self):
        """Returns true if the essential outputs are found on disk."""
        # SC, GSC, and GP always create an _ETL for the input spreadsheet
        cleaned_path = os.path.join(self.userfiles_dir, \
            get_cleaned_spreadsheet_relative_path(\
                self.run_directory_relative_path,
                self.input_spreadsheet_file_dto))
        # SC, GSC, and GP always create a _MAP for the input spreadsheet
        map_path = os.path.join(self.userfiles_dir, \
            get_gene_names_map_relative_path(\
                self.run_directory_relative_path,
                self.input_spreadsheet_file_dto))
        # progress check
        return_val = os.path.isfile(cleaned_path) and os.path.isfile(map_path)
        # if there was a phenotype file, we also expect an _ETL for it
        if self.input_phenotype_file_dto is not None:
            pheno_path = os.path.join(self.userfiles_dir, \
                get_cleaned_spreadsheet_relative_path(\
                    self.run_directory_relative_path,
                    self.input_phenotype_file_dto))
            return_val = return_val and os.path.isfile(pheno_path)
        return return_val

    def on_done(self):
        """Deletes self from Chronos."""
        self.delete_from_chronos()

def get_cleaned_spreadsheet_relative_path(\
        run_directory_relative_path, file_dto):
    """Given an EveEntry representing an input spreadsheet and the
    run_directory_relative_path for a data_cleanup job, returns the relative
    path to the cleaned spreadsheet.

    Args:
        run_directory_relative_path (str): The relative path from userfiles_dir
            to the run directory for the data_cleanup job.
        file_dto (FileDTO): The dto representing the input spreadsheet
            database record.

    Returns:
        str: The relative path from the data cleanup working directory to the
            file.
    """
    filename = file_dto.get_nest_id().to_slug()
    #eve_entry.get_eve_attributes().get_eve_id().get_value()
    cleaned_filename = filename + '_ETL.tsv'
    full_path = os.path.join(run_directory_relative_path, cleaned_filename)
    return full_path

def get_gene_names_map_relative_path(\
        run_directory_relative_path, file_dto):
    """Given an EveEntry representing an input spreadsheet and the
    run_directory_relative_path for a data_cleanup job, returns the relative
    path to the cleaned spreadsheet.

    Args:
        run_directory_relative_path (str): The relative path from userfiles_dir
            to the run directory for the data_cleanup job.
        file_dto(file_dto): The FileDTO for the db record representing the input
            spreadsheet.

    Returns:
        str: The relative path from the data cleanup working directory to the
            file.
    """
    #filename = eve_entry.get_eve_attributes().get_eve_id().get_value()
    filename = file_dto.get_nest_id().to_slug()
    cleaned_filename = filename + '_MAP.tsv'
    return os.path.join(run_directory_relative_path, cleaned_filename)

def get_relative_path_to_uploaded_file(file_dto):
    """Returns the relative path from the data cleanup working directory, which
    is assumed to be two levels beneath userfiles_dir, to a file represented by
    an EveEntry.

    Args:
        file_dto(FileDTO): Represents the db record representing the file.

    Returns:
        str: The relative path from the data cleanup working directory to the
            file.

    """
    file_id = file_dto.get_nest_id()
    project_id = file_dto.project_id
    userfiles_dir = '../../'
    path = files.full_file_path(userfiles_dir, project_id, file_id)
    return path

def get_dict_from_id_to_name(map_file_path):
    """Returns a dict in which the keys are gene ids and the values are gene
    names if the spreadsheet has been preprocessed. Returns None otherwise.

    Args:

        map_file_path (str): The path to the gene-name map file.

    Returns:
        dict: A dict in which the keys are gene ids and the values are gene
            names, unless the spreadsheet hasn't been preprocessed, in which
            case will return None.

    """
    return_val = None
    if os.path.isfile(map_file_path):
        with open(map_file_path, 'r') as infile:
            lines = [line.rstrip().split('\t') for line in infile]
        return_val = {pair[0]: pair[1] for pair in lines if len(pair) == 2}
    return return_val

def create_dummy_mapping(infile_path, outfile_path):
    """Given the path to an input_spreadsheet as infile_path, generates
    a dummy mapping file from ensembl id to ensembl id for use with pipelines
    that want to map input names internally.

    Args:
        infile_path (str): The path to an input_spreadsheet.
        outfile_path (str): The path to a new file to contain the dummy mapping.

    Returns:
        None.

    """
    # have seen this file become visible on the nest host before its contents
    # are fully synced with those of the node that produced them
    # that causes a StopIteration error, which we'll catch so we can retry
    # TODO make real plans to ensure data consistency between nodes
    num_attempts = 3
    attempt_wait_seconds = 5
    for attempt in range(0, num_attempts):
        try:
            with open(infile_path, 'rb') as infile:
                csvreader = csv.reader(infile, delimiter='\t')
                csvreader.next() # skip the header
                with open(outfile_path, 'w') as outfile:
                    for row in csvreader:
                        outfile.write(row[0] + '\t'+ row[0] + '\n')
                break
        except StopIteration:
            LOGGER.warning("StopIteration in create_dummy_mapping on " + \
                "attempt " + str(attempt) + ". Retrying in " + \
                str(attempt_wait_seconds) + " seconds.")
            sleep(attempt_wait_seconds)
