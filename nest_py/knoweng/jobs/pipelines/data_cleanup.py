"""
This module defines a class for running knoweng's spreadsheet preprocess jobs.
"""
import csv
from enum import Enum
import logging
import os
from time import sleep

import yaml

from nest_py.knoweng.jobs.pipeline_job import PipelineJob
import nest_py.knoweng.data_types.files as files

PipelineType = Enum('PipelineType', \
    'FEATURE_PRIORITIZATION GENE_SET_CHARACTERIZATION SAMPLE_CLUSTERING SIGNATURE_ANALYSIS')
CorrelationMeasure = Enum('CorrelationMeasure', 'T_TEST PEARSON EDGER')
MissingValuesMethod = Enum('MissingValuesMethod', 'AVERAGE REMOVE REJECT')

LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.INFO)

class DataCleanupJob(PipelineJob):
    """Subclass of PipelineJob that handles data cleanup jobs."""
    def __init__(self, user_id, job_id, project_id, userfiles_dir, timeout,
                 cloud, species_id, input_spreadsheet_file_dto,
                 input_phenotype_file_dto, gg_network_name_full_path,
                 run_directory_relative_path, pipeline_type,
                 correlation_measure, missing_values_method):
        """Initializes self.

        Args:
            user_id (NestId): The user id associated with the job.
            job_id (Nestid): The job id associated with the job.
            project_id (Nestid): The project id associated with the job.
            userfiles_dir (str): The base directory containing all files for
                all users.
            timeout (int): The maximum execution time in seconds.
            cloud (str): The cloud name, which must appear as a key in
                your executor's cloud_path_dict.
            species_id (str): The species_id to use when looking up gene names.
            input_spreadsheet_file_dto (FileDTO):
                The spreadsheet file's database record.
            input_phenotype_file_dto (FileDTO):
                The phenotype file's database record (or for SA, the signatures
                file's database record), or None if there is no phenotype file.
                TODO refactor this, but would be nice if pipelines were
                refactored first.
            gg_network_name_full_path (str): The path to the gene-gene network
                edge file. Used for clustering and prioritization to distinguish
                KN mode from non-KN mode. Passed along to DCP docker image for
                only sample clustering with network smoothing.
            run_directory_relative_path (str): The relative path from
                userfiles_dir to the run directory for the data cleanup job.
                Must already exist.
            pipeline_type (PipelineType): The pipeline type.
            correlation_measure (CorrelationMeasure): If pipeline_type is
                FEATURE_PRIORITIZATION, then the correlation measure, else None.
            missing_values_method (MissingValuesMethod): If pipeline_type is
                FEATURE_PRIORITIZATION, then the missing values method, else
                None.

        Returns:
            None: None.

        """
        self.input_spreadsheet_file_dto = input_spreadsheet_file_dto
        self.input_phenotype_file_dto = input_phenotype_file_dto
        self.gg_network_name_full_path = gg_network_name_full_path
        self.run_directory_relative_path = run_directory_relative_path

        input_spreadsheet_relative_path = \
            get_relative_path_to_uploaded_file(self.input_spreadsheet_file_dto)

        input_phenotype_relative_path = None
        if input_phenotype_file_dto is not None:
            input_phenotype_relative_path = \
                get_relative_path_to_uploaded_file(input_phenotype_file_dto)

        image = 'knowengdev/data_cleanup_pipeline:09_21_2019'

        # create yaml file
        redis_params = PipelineJob.get_cloud_redis_dict(cloud)
        run_data = {
            'spreadsheet_name_full_path': input_spreadsheet_relative_path,
            'results_directory': './',
            'taxonid': species_id,
            'source_hint': '',
            'redis_credential': {
                'host': redis_params['host'],
                'port': redis_params['port'],
                'password': redis_params['password']
            },
            'docker_image': image
        }
        if input_phenotype_relative_path is not None:
            run_data['phenotype_name_full_path'] = input_phenotype_relative_path
        if pipeline_type is PipelineType.FEATURE_PRIORITIZATION:
            if gg_network_name_full_path is None:
                self.pipeline_type = 'feature_prioritization_pipeline'
                run_data['threshold'] = 2
            else:
                self.pipeline_type = 'gene_prioritization_pipeline'
            if correlation_measure is CorrelationMeasure.T_TEST:
                run_data['correlation_measure'] = 't_test'
            elif correlation_measure is CorrelationMeasure.PEARSON:
                run_data['correlation_measure'] = 'pearson'
            elif correlation_measure is CorrelationMeasure.EDGER:
                run_data['correlation_measure'] = 'edgeR'
            else:
                # TODO report error
                pass
            if missing_values_method is MissingValuesMethod.AVERAGE:
                run_data['impute'] = 'average'
            elif missing_values_method is MissingValuesMethod.REMOVE:
                run_data['impute'] = 'remove'
            elif missing_values_method is MissingValuesMethod.REJECT:
                run_data['impute'] = 'reject'
            else:
                # TODO report error
                pass
        elif pipeline_type is PipelineType.GENE_SET_CHARACTERIZATION:
            self.pipeline_type = 'geneset_characterization_pipeline'
        elif pipeline_type is PipelineType.SAMPLE_CLUSTERING:
            if gg_network_name_full_path is None:
                self.pipeline_type = 'general_clustering_pipeline'
            else:
                self.pipeline_type = 'samples_clustering_pipeline'
                run_data['gg_network_name_full_path'] = gg_network_name_full_path
        elif pipeline_type is PipelineType.SIGNATURE_ANALYSIS:
            self.pipeline_type = 'signature_analysis_pipeline'
            run_data['signature_name_full_path'] = input_phenotype_relative_path
            del run_data['phenotype_name_full_path']
        else:
            # TODO report error
            pass
        run_data['pipeline_type'] = self.pipeline_type

        self.run_file_path = os.path.join(\
            userfiles_dir, run_directory_relative_path, 'run_cleanup.yml')
        with open(self.run_file_path, 'wb') as outfile:
            yaml.safe_dump(run_data, outfile, default_flow_style=False)

        cleanup_job_name = 'nest-data-cleanup-' + job_id.to_slug().lower()
        LOGGER.debug(cleanup_job_name + '.__init__')
        super(DataCleanupJob, self).__init__(\
            user_id, job_id, project_id, userfiles_dir,\
            run_directory_relative_path, cleanup_job_name, timeout, cloud,\
            image, 1, 10000)

    def get_command(self):
        """Returns the docker command for data_cleanup."""
        LOGGER.debug(self.job_name + '.get_command')
        cd_path = os.path.join(PipelineJob.get_cloud_path(self.cloud),\
            'userfiles', self.run_directory_relative_path)
        return 'date && cd ' + cd_path + \
            ' && python3 /home/src/data_cleanup.py ' + \
            ' -run_directory ./' + \
            ' -run_file run_cleanup.yml' + \
            ' && date;'

    def is_ready(self):
        """Returns True always."""
        LOGGER.debug(self.job_name + '.is_ready? True')
        return True

    def is_failed(self):
        """Returns True if the pipeline reported an error."""
        error_message = self.get_error_message()
        if error_message is not None:
            LOGGER.warning(self.job_name + '.is_failed? ' + error_message)
        else:
            LOGGER.debug(self.job_name + '.is_failed? False')
        return error_message is not None

    def get_error_message(self):
        """Returns the error messages reported by the pipeline, if any."""
        LOGGER.debug(self.job_name + '.get_error_message')
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
        # SC, GSC, and FP always create an _ETL for the input spreadsheet
        cleaned_path = os.path.join(self.userfiles_dir, \
            get_cleaned_spreadsheet_relative_path(\
                self.run_directory_relative_path,
                self.input_spreadsheet_file_dto))
        # progress check
        return_val = os.path.isfile(cleaned_path)
        # SC and FP create a _MAP for the input spreadsheet if there's a gg net
        # GSC always creates a _MAP
        if self.gg_network_name_full_path is not None or self.pipeline_type == \
            'geneset_characterization_pipeline':
            map_path = os.path.join(self.userfiles_dir, \
                get_gene_names_map_relative_path(\
                    self.run_directory_relative_path,
                    self.input_spreadsheet_file_dto))
            return_val = return_val and os.path.isfile(map_path)
        # if there was a phenotype file, we also expect an _ETL for it
        if self.input_phenotype_file_dto is not None:
            pheno_path = os.path.join(self.userfiles_dir, \
                get_cleaned_spreadsheet_relative_path(\
                    self.run_directory_relative_path,
                    self.input_phenotype_file_dto))
            return_val = return_val and os.path.isfile(pheno_path)
        LOGGER.debug(self.job_name + '.is_done? ' + str(return_val))
        return return_val

    def on_done(self):
        """Deletes self from executor."""
        LOGGER.debug(self.job_name + '.on_done')
        self.delete_job_record()

    def get_run_file_path(self):
        """Returns the full path to the run file."""
        return self.run_file_path

def get_cleaned_spreadsheet_relative_path(\
        run_directory_relative_path, file_dto):
    """Given a FileDTO representing an input spreadsheet and the
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
    cleaned_filename = filename + '_ETL.tsv'
    full_path = os.path.join(run_directory_relative_path, cleaned_filename)
    return full_path

def get_gene_names_map_relative_path(\
        run_directory_relative_path, file_dto):
    """Given a FileDTO representing an input spreadsheet and the
    run_directory_relative_path for a data_cleanup job, returns the relative
    path to the gene map.

    Args:
        run_directory_relative_path (str): The relative path from userfiles_dir
            to the run directory for the data_cleanup job.
        file_dto(file_dto): The FileDTO for the db record representing the input
            spreadsheet.

    Returns:
        str: The relative path from the data cleanup working directory to the
            file.
    """
    filename = file_dto.get_nest_id().to_slug()
    map_filename = filename + '_MAP.tsv'
    return os.path.join(run_directory_relative_path, map_filename)

def get_gene_names_mapped_and_unmapped_relative_path(\
        run_directory_relative_path, file_dto):
    """Given a FileDTO representing an input spreadsheet and the
    run_directory_relative_path for a data_cleanup job, returns the relative
    path to the table of all mapped and unmapped names.

    Args:
        run_directory_relative_path (str): The relative path from userfiles_dir
            to the run directory for the data_cleanup job.
        file_dto(file_dto): The FileDTO for the db record representing the input
            spreadsheet.

    Returns:
        str: The relative path from the data cleanup working directory to the
            file.
    """
    filename = file_dto.get_nest_id().to_slug()
    unmapped_filename = filename + '_User_To_Ensembl.tsv'
    return os.path.join(run_directory_relative_path, unmapped_filename)

def get_relative_path_to_uploaded_file(file_dto):
    """Returns the relative path from the data cleanup working directory, which
    is assumed to be two levels beneath userfiles_dir, to a file represented by
    a FileDTO.

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

def get_dict_from_id_to_name(map_file_path, gg_network_node_map_full_path):
    """Returns a dict in which the keys are gene ids and the values are gene
    names if the spreadsheet has been preprocessed. Returns an empty dict
    otherwise.

    Args:
        map_file_path (str): The path to the gene-name map file created by a
            data cleanup job.
        gg_network_node_map_full_path (str): The path to the Knowledge Network's
            gene-gene network node-map file associated with the
            gg_network_name_full_path provided for the analysis. Used to map
            any genes introduced by the analysis--i.e., not present in the
            user's original data. Pass None if no gg_network_name_full_path was
            provided for the analysis.

    Returns:
        dict: A dict in which the keys are gene ids and the values are gene
            names, unless the spreadsheet hasn't been preprocessed, in which
            case will return None.

    """
    return_val = {}
    check_dcp_map = os.path.isfile(map_file_path)
    check_kn_map = check_dcp_map and gg_network_node_map_full_path is not None \
        and os.path.isfile(gg_network_node_map_full_path)
    # process kn map first, so that dcp mapping can override its mappings
    if check_kn_map:
        with open(gg_network_node_map_full_path, 'r') as infile:
            lines = [line.rstrip().split('\t') for line in infile]
            return_val.update(\
                {line[1]: line[3] for line in lines})
    if check_dcp_map:
        with open(map_file_path, 'r') as infile:
            lines = [line.rstrip().split('\t') for line in infile]
            return_val.update(\
                {pair[0]: pair[1] for pair in lines if len(pair) == 2})
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

def map_first_column_of_file(inpath, outpath, in_string_to_out_string):
    """Transforms the TSV file at `inpath` by mapping values in the first column
    according to `in_string_to_out_string`, saving the result at `outpath`.
    Preserves the first row, which is assumed to contain headers. (Can always
    add a flag parameter for that if we need it.)

    Args:
        inpath (str): The path to the input TSV file.
        outpath (str): The path at which to write the output TSV file.
        in_string_to_out_string (dict): The mapping from strings in `inpath` to
            the strings in `outpath`. This method will preserve any `inpath`
            values that aren't keys in the dict.

    Returns:
        None.

    """
    preserve_next_row = True
    with open(outpath, 'w') as outfile:
        with open(inpath, 'r') as infile:
            for line in infile:
                if preserve_next_row:
                    outfile.write(line)
                    preserve_next_row = False
                else:
                    pieces = line.split("\t", 1)
                    outfile.write(\
                        in_string_to_out_string.get(pieces[0], pieces[0]) + \
                        "\t" + pieces[1])
