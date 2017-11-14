"""
This module defines a class for running knoweng's spreadsheet preprocess jobs.
"""
import csv
import os
import yaml
from nest_py.knoweng.jobs.chronos_job import ChronosJob

class PastedGeneSetConversionJob(ChronosJob):
    """Subclass of ChronosJob that handles pasted gene sets."""
    def __init__(self, user_id, job_id, userfiles_dir, job_dir_relative_path, \
            timeout, cloud, file_dto, species_id):
        """Initializes self.

        Args:
            user_id (NestId): The user id associated with the job.
            job_id (NestId): The unique identifier Eve/Mongo assigns to the job.
            userfiles_dir (str): The base directory containing all files for
                all users.
            job_dir_relative_path (str): The relative directory from
                userfiles_dir to the working directory, which must already
                exist.
            timeout (int): The maximum execution time in seconds.
            cloud (str): The cloud name, which must appear as a key in
                nest_py.knoweng.jobs.ChronosJob.cloud_path_dict.
            file_dto (FileDTO): The file created from the user's pasted data.
            species_id (str): The species_id to use when looking up gene names.

        Returns:
            None: None.

        """
        self.species_id = species_id
        self.file_dto = file_dto

        job_name = 'nest_pasted_gene_set_conversion_' +  job_id.to_slug()

        self.job_dir_path = os.path.join(userfiles_dir, job_dir_relative_path)

        # create temp_redis_vector
        # TODO only need to do this once per species
        species_nodes_path = os.path.join('/networks', 'Species', species_id,\
            species_id + '.node_map.txt')
        universe = set()
        with open(species_nodes_path, 'r') as infile:
            for row in csv.reader(infile, delimiter='\t'):
                universe.add(row[1])
        universe_filename = 'universe.txt'
        universe_path = os.path.join(self.job_dir_path, universe_filename)
        with open(universe_path, 'w') as outfile:
            for gene in universe:
                outfile.write(gene + '\n')

        # create yaml file
        redis_params = ChronosJob.cloud_redis_dict[cloud]
        run_data = {
            'pasted_gene_list_full_path': file_dto.get_file_path('../../'),
            'results_directory': './',
            'temp_redis_vector': universe_filename,
            'redis_credential': {
                'host': redis_params['host'],
                'port': redis_params['port'],
                'password': redis_params['password']
            },
            'source_hint': '',
            'taxonid': species_id
        }

        yml_path = os.path.join(self.job_dir_path, 'run_pasted.yml')
        with open(yml_path, 'wb') as outfile:
            yaml.safe_dump(run_data, outfile, default_flow_style=False)

        super(PastedGeneSetConversionJob, self).__init__(\
            user_id, job_id, userfiles_dir, job_dir_relative_path, job_name,
            timeout, cloud, 'knowengdev/data_cleanup_pipeline:07_26_2017', 1,
            4000)

    def get_command(self):
        """Returns the docker command for spreadsheet_preprocess."""
        cd_path = os.path.join(ChronosJob.cloud_path_dict[self.cloud], \
            'userfiles', self.job_dir_relative_path)
        return 'date && cd ' + cd_path + \
            ' && python3 /home/src/pasted_gene_cleanup.py ' + \
            ' -run_directory ./' + \
            ' -run_file run_pasted.yml' + \
            ' && date;'

    def is_ready(self):
        """Returns true always."""
        return True

    def is_done(self):
        """Returns true if outfile.df is found on disk."""
        etl_file_path = os.path.join(self.job_dir_path, \
            self.get_output_gene_set_filename())
        map_file_path = os.path.join(self.job_dir_path, \
            self.get_output_gene_map_filename())
        return os.path.isfile(etl_file_path) and os.path.isfile(map_file_path)

    def on_done(self):
        """Deletes self from Chronos."""
        self.delete_from_chronos()

    def get_output_gene_set_filename(self):
        """Returns name of gene-set file produced by the pipeline."""
        return self.file_dto.get_nest_id().to_slug() + '_ETL.tsv'

    def get_output_gene_map_filename(self):
        """Returns name of gene-set map file produced by the pipeline."""
        return self.file_dto.get_nest_id().to_slug() + '_MAP.tsv'
