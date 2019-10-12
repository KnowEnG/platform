"""This module defines a class for running knoweng's signature analysis jobs."""
import csv
import logging
import os
from zipfile import ZipFile, ZIP_DEFLATED

import yaml

from nest_py.knoweng.jobs.pipeline_job import PipelineJob
from nest_py.knoweng.jobs.db_utils import create_sa_record, get_file_record,\
    create_file_record
from nest_py.knoweng.jobs.pipelines.data_cleanup import \
    DataCleanupJob, PipelineType, get_cleaned_spreadsheet_relative_path

LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.INFO)

class SignatureAnalysisJob(PipelineJob):
    """Subclass of PipelineJob that handles signature analysis jobs."""
    def __init__(self, user_id, job_id, project_id, userfiles_dir,
                 job_dir_relative_path, timeout, cloud,
                 query_file_relative_path, signatures_file_relative_path,
                 similarity_measure, prep_job):
        """Initializes self.

        Args:
            user_id (NestId): The user id associated with the job.
            job_id (NestId): The job id associated with the job.
            project_id (NestId): The project id associated with the job.
            userfiles_dir (str): The base directory containing all files for
                all users.
            job_dir_relative_path (str): The relative path from userfiles_dir to
                the directory containing the job's files, which must already
                exist.
            timeout (int): The maximum execution time in seconds.
            cloud (str): The cloud name, which must appear as a key in
                your executor's cloud_path_dict.
            query_file_relative_path (str): The relative path from the
                userfiles_dir to the features file.
            signatures_file_relative_path (str): The relative path from the
                userfiles_dir to the signatures file.
            correlation_method (str): One of ['pearson', 'spearman', 'cosine'].
            prep_job (DataCleanupJob): The job that prepares the inputs.

        Returns:
            None: None.

        """
        job_name = 'nest-sa-' + similarity_measure + '-' + \
            job_id.to_slug().lower()
        LOGGER.debug(job_name + '.__init__')

        self.query_file_relative_path = query_file_relative_path
        self.signatures_file_relative_path = signatures_file_relative_path
        self.prep_job = prep_job

        self.job_dir_path = os.path.join(userfiles_dir, job_dir_relative_path)

        self.results_dir_path = os.path.join(self.job_dir_path, 'results')
        os.mkdir(self.results_dir_path)

        # create yaml file
        image = 'knowengdev/signature_analysis_pipeline:05_10_2018'
        run_data = {
            'method': 'similarity',
            'similarity_measure': similarity_measure,
            'spreadsheet_name_full_path': '../../' + query_file_relative_path,
            'signature_name_full_path': '../../' + signatures_file_relative_path,
            'results_directory': './results',
            'tmp_directory': './tmp',
            'docker_image': image
        }

        self.yml_path = os.path.join(self.job_dir_path, 'run.yml')
        with open(self.yml_path, 'wb') as outfile:
            yaml.safe_dump(run_data, outfile, default_flow_style=False)

        # note AWS m4.xl is 4 CPUS, 16 GB
        super(SignatureAnalysisJob, self).__init__(\
            user_id, job_id, project_id, userfiles_dir, job_dir_relative_path, \
            job_name, timeout, cloud, image, 4, 14500)

    def get_command(self):
        """Returns the docker command for signature analysis."""
        LOGGER.debug(self.job_name + '.get_command')
        return 'date && cd ' + \
            os.path.join(PipelineJob.get_cloud_path(self.cloud), \
                'userfiles', self.job_dir_relative_path) + \
            ' && python3 /home/src/gene_signature.py ' + \
            ' -run_directory ./' + \
            ' -run_file run.yml' + \
            ' && date;'

    def is_ready(self):
        """Returns true iff preprocessing is done."""
        return_val = self.prep_job.is_done()
        LOGGER.debug(self.job_name + '.is_ready? ' + str(return_val))
        return return_val

    def is_done(self):
        """Returns true iff all of the files have been created."""
        return_val = self.find_result_file() is not None and \
            self.find_association_file() is not None
        LOGGER.debug(self.job_name + '.is_done? ' + str(return_val))
        return return_val

    def find_result_file(self):
        """Searches for result file produced by pipeline. If the file is found,
        returns the file path, else returns None.

            Returns:
                str: The path to the file if found, else None.

        """
        return_val = None
        for name in os.listdir(self.results_dir_path):
            if name.startswith('result_'):
                return_val = os.path.join(self.results_dir_path, name)
        return return_val

    def find_association_file(self):
        """Searches for association file produced by pipeline. If the file is
        found, returns the file path, else returns None.

            Returns:
                str: The path to the file if found, else None.

        """
        return_val = None
        for name in os.listdir(self.results_dir_path):
            if name.startswith('Gene_to_TF_Association_'):
                return_val = os.path.join(self.results_dir_path, name)
        return return_val

    def on_done(self):
        """Processes scores, loads data to database, prepares zip file, and
        deletes self from the executor.

            Returns:
                None: None.

        """
        LOGGER.debug(self.job_name + '.on_done')
        scores = {}
        seen_header = False
        with open(self.find_result_file(), 'rb') as csvfile:
            # columns are signatures, rows are samples
            # TODO this isn't the most compact representation, but it's easy
            for row in csv.reader(csvfile, delimiter='\t'):
                if not seen_header:
                    signature_names = row[1:]
                    for name in signature_names:
                        scores[name] = {}
                    seen_header = True
                else:
                    sample_name = row[0]
                    signature_values = [float(val) for val in row[1:]]
                    for position, signature_name in enumerate(signature_names):
                        scores[signature_name][sample_name] = \
                            signature_values[position]
        create_sa_record(self.user_id, self.job_id, scores)
        output_file_info = self.prepare_output_files()
        self.capture_files_in_db(output_file_info)
        self.capture_files_in_zip(output_file_info)
        self.delete_job_record()

    def prepare_output_files(self):
        """Transforms output files in preparation for capture as new file
        records in the DB and/or as members of the download zip.

         Returns:
           list: A list of dicts. Each dict represents a single output file and
               contains keys 'path', 'name', 'in_db', and 'in_zip'.

         """
        output_file_info = []

        cleaned_query_path = os.path.join(\
            self.userfiles_dir, self.query_file_relative_path)
        output_file_info.append({
            'path': cleaned_query_path,
            'name': 'clean_samples_matrix.txt',
            'in_db': False,
            'in_zip': True
        })

        cleaned_signatures_path = os.path.join(\
            self.userfiles_dir, self.signatures_file_relative_path)
        output_file_info.append({
            'path': cleaned_signatures_path,
            'name': 'clean_signatures_matrix.txt',
            'in_db': False,
            'in_zip': True
        })

        output_file_info.append({
            'path': self.find_result_file(),
            'name': 'similarity_matrix.tsv',
            'in_db': True,
            'in_zip': True
        })
        output_file_info.append({
            'path': self.find_association_file(),
            'name': 'similarity_matrix.binary.tsv',
            'in_db': True,
            'in_zip': True
        })

        output_file_info.append({
            'path': '/pipeline_readmes/README-SA.md',
            'name': 'README-SA.md',
            'in_db': False,
            'in_zip': True
        })
        output_file_info.append({
            'path': self.yml_path,
            'name': 'run_params.yml',
            'in_db': False,
            'in_zip': True
        })
        output_file_info.append({
            'path': self.prep_job.get_run_file_path(),
            'name': 'run_cleanup_params.yml',
            'in_db': False,
            'in_zip': True
        })

        return output_file_info

    def capture_files_in_db(self, output_file_info):
        """Creates database records for some of the outputs, so they'll appear
        in the interface as files.

        Args:
            output_file_info (list): The list returned by prepare_output_files.

        Returns:
            None.

        """
        for item in output_file_info:
            if item['in_db']:
                create_file_record(\
                    self.user_id, self.job_id, self.project_id,\
                    self.userfiles_dir, item['path'], item['name'])

    def capture_files_in_zip(self, output_file_info):
        """Creates a zip file on disk for later download by the user.

        Args:
            output_file_info (list): The list returned by prepare_output_files.

        Returns:
            None.

        """
        zip_path = os.path.join(self.job_dir_path, 'download.zip')
        with ZipFile(zip_path, 'w', ZIP_DEFLATED) as zipout:
            for item in output_file_info:
                if item['in_zip']:
                    zipout.write(item['path'], item['name'])

def get_signature_analysis_runners(\
    user_id, job_id, project_id, userfiles_dir, project_dir, timeout, cloud,\
    query_file_id, signatures_file_id, similarity_measure):
    """Returns a list of PipelineJob instances required to run an SA job.

    Args:
        user_id (NestId): The user id associated with the job.
        job_id (NestId): The job id associated with the job.
        project_id (NestId): The project id associated with the job.
        userfiles_dir (str): The base directory containing all files for
            all users.
        project_dir (str): The name of the directory containing the files
            associated with the current project.
        timeout (int): The maximum execution time in seconds.
        cloud (str): The cloud name, which must appear as a key in
            your executor's cloud_path_dict.
        query_file_id (NestId): The _id of the query file in the database.
        signatures_file_id (NestId): The _id of the signatures file in the
            database.
        similarity_measure (str): One of ['pearson', 'spearman', 'cosine'].

    Returns:
        list: A list of PipelineJob instances required to run an SA job.

    """
    job_name = "nest-sa-" + similarity_measure + '-' + job_id.to_slug().lower()
    job_dir_relative_path = os.path.join(project_dir, job_name)
    os.mkdir(os.path.join(userfiles_dir, job_dir_relative_path))

    query_file_dto = get_file_record(user_id, query_file_id)
    cleaned_query_file_relative_path = \
        get_cleaned_spreadsheet_relative_path(\
            job_dir_relative_path, query_file_dto)

    signatures_file_dto = get_file_record(user_id, signatures_file_id)
    cleaned_signatures_file_relative_path = \
        get_cleaned_spreadsheet_relative_path(\
            job_dir_relative_path, signatures_file_dto)

    prep_job = DataCleanupJob(\
        user_id, job_id, project_id, userfiles_dir, timeout, cloud, 0,
        query_file_dto, signatures_file_dto, None, job_dir_relative_path,
        PipelineType.SIGNATURE_ANALYSIS, None, None)
    return [
        prep_job,
        SignatureAnalysisJob(\
            user_id, job_id, project_id, userfiles_dir, job_dir_relative_path,
            timeout, cloud, cleaned_query_file_relative_path,
            cleaned_signatures_file_relative_path, similarity_measure,
            prep_job)
    ]
