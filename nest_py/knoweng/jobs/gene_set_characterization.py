"""This module defines a class for running knoweng's gene set characterization jobs."""

import csv
import os
from zipfile import ZipFile, ZIP_DEFLATED

import pandas as pd
import yaml

from nest_py.knoweng.jobs.chronos_job import \
    ChronosJob, get_all_chronos_job_names, delete_from_chronos_by_name
from nest_py.knoweng.jobs.db_utils import create_gsc_record, get_file_record
from nest_py.knoweng.jobs.networks import get_merged_network_info
from nest_py.knoweng.jobs.pasted_gene_set_conversion import \
    PastedGeneSetConversionJob
from nest_py.knoweng.jobs.data_cleanup import \
    DataCleanupJob, PipelineType, get_cleaned_spreadsheet_relative_path, \
    get_gene_names_map_relative_path, create_dummy_mapping

class GeneSetCharacterizationJob(ChronosJob):
    """Subclass of ChronosJob that handles gene set characterization jobs."""
    def __init__(self, user_id, job_id, userfiles_dir, job_dir_relative_path,
                 timeout, cloud, species_id, cleaned_gene_set_file_relative_path,
                 gene_names_map_relative_path, gene_collections, method,
                 network_name, network_smoothing, prep_job):
        """Initializes self.

        Args:
            user_id (NestId): The user id associated with the job.
            job_id (NestId): The unique identifier Eve/Mongo assigns to the job.
            userfiles_dir (str): The base directory containing all files for
                all users.
            job_dir_relative_path (str): The relative path from userfiles_dir to
                the directory containing the job's files, which must already
                exist.
            timeout (int): The maximum execution time in seconds.
            cloud (str): The cloud name, which must appear as a key in
                nest_py.knoweng.jobs.ChronosJob.cloud_path_dict.
            species_id (str): The species_id to disambiguate networks with
                identical edge_type_names.
            cleaned_gene_set_file_relative_path (str): The relative path from
                userfiles_dir to the cleaned gene-set file.
            gene_names_map_relative_path (str): The relative path from
                userfiles_dir to the gene-names map.
            gene_collections (list): The name of the public gene collections to
                compare.
            method (str): One of ['Fisher', 'DRaWR'].
            network_name (str): The interaction network to use with
                network-based methods.
            network_smoothing (float): The amount of network smoothing to apply.
            prep_job (ChronosJob): The DataCleanupJob or
                PastedGeneSetConversionJob that will prepare the data for this
                job.

        Returns:
            None: None.

        """
        self.cleaned_gene_set_file_relative_path = \
            cleaned_gene_set_file_relative_path
        self.gene_names_map_relative_path = gene_names_map_relative_path
        self.method = method
        self.prep_job = prep_job

        networks = get_merged_network_info('/networks/')

        self.job_dir_path = os.path.join(userfiles_dir, job_dir_relative_path)

        # create dummy mapping, since our input file has already been cleaned
        # don't actually create the file until `start` call, because gene-name
        # mapping may not have produced cleaned_gene_set_file_relative_path yet
        self.dummy_map_name = 'dummy_map.tsv'

        # create yaml files
        self.subjob_dir_name = 'subjobs'
        self.subjob_chronos_name = job_id.to_slug() + 'child'
        self.subjob_dir_path = os.path.join(\
            self.job_dir_path, self.subjob_dir_name)
        os.mkdir(self.subjob_dir_path)
        run_data = {
            'spreadsheet_name_full_path': '../../../' + \
                cleaned_gene_set_file_relative_path,
            'gene_names_map': '../' + self.dummy_map_name
        }
        if method == 'Fisher':
            run_data['method'] = 'fisher'
            self.gg_network_metadata_full_path = None
        elif method == 'DRaWR':
            run_data['method'] = 'DRaWR'
            run_data['rwr_max_iterations'] = 500
            run_data['rwr_convergence_tolerence'] = 1.0e-4
            run_data['rwr_restart_probability'] = \
                1- float(network_smoothing)/100
            gg_info = [net for net in networks if \
                net['species_id'] == species_id and \
                net['edge_type_name'] == network_name][0]
            run_data['gg_network_name_full_path'] = '../../../../networks/' + \
                gg_info['path_to_edge']
            self.gg_network_metadata_full_path = '../../../../networks/' + \
                gg_info['path_to_metadata']
        else:
            raise ValueError('Unknown method ' + method)

        # create a mapping from collection name to network info
        self.collection_to_network = {}
        for collection in gene_collections:
            network_info = [net for net in networks if \
                net['species_id'] == species_id and \
                net['edge_type_name'] == collection][0]
            self.collection_to_network[collection] = network_info

            run_data['results_directory'] = './' + collection + '_results'
            run_data['pg_network_name_full_path'] = '../../../../networks/' + \
                network_info['path_to_edge']

            with open(self.yml_path_for_collection(collection), 'wb') as outfile:
                yaml.safe_dump(run_data, outfile, default_flow_style=False)

        job_name = 'nest_GSC_' + job_id.to_slug()
        super(GeneSetCharacterizationJob, self).__init__(\
            user_id, job_id, userfiles_dir, job_dir_relative_path,
            job_name, timeout, cloud,
            'mepsteindr/pipeline_utilities:20170713', 1, 1000)

    def yml_path_for_collection(self, collection):
        """Returns the yml file path for a collection's subjob.

        Args:
            collection (str): The name of the collection.

        Returns:
            str: The path to the yml file for the collection's subjob.

        """
        return os.path.join(self.subjob_dir_path, collection + '.yml')

    def get_command(self):
        """Returns the docker command for gene_set_characterization."""
        # TODO benchmark to set mem and cpu according to inputs
        # -gm 5000 below means 5GB mem
        return 'date && ' + \
            'python3 /home/src/pipelines/pipeline_utilities.py GSC' + \
            ' -gt 07_26_2017' + \
            ' -gm 7000' + \
            ' -gto ' + str(self.timeout) + \
            ' -c ' + ChronosJob.cloud_mesos_dict[self.cloud] + \
            ' -sd ' + ChronosJob.cloud_path_dict[self.cloud] + \
            ' -lp logs' + \
            ' -uid ' + self.subjob_chronos_name + \
            ' -gyd userfiles/' + \
            os.path.join(self.job_dir_relative_path, self.subjob_dir_name) + \
            ' && date;'

    def is_ready(self):
        return self.prep_job.is_done()

    def start(self):
        dummy_in_path = os.path.join(\
            self.userfiles_dir, self.cleaned_gene_set_file_relative_path)
        dummy_out_path = os.path.join(self.job_dir_path, self.dummy_map_name)
        create_dummy_mapping(dummy_in_path, dummy_out_path)
        super(GeneSetCharacterizationJob, self).start()

    def is_done(self):
        return os.path.isfile(os.path.join(\
            self.subjob_dir_path, 'done.txt'))

    def on_done(self):
        """Processes scores, loads data to database, prepares zip file, and
        deletes self and children from Chronos.

            Returns:
                None: None.

        """
        user_gene_sets = self.get_user_gene_sets()
        set_level_scores = self.get_set_level_scores(user_gene_sets)
        create_gsc_record(self.user_id, self.job_id, user_gene_sets, \
            set_level_scores, self.get_minimum_score())
        self.prepare_zip_file()
        # we don't know the exact names of the child jobs--need to fetch the
        # list of all chronos jobs and filter by name
        all_chronos_jobs = get_all_chronos_job_names(self.cloud)
        for chronos_job in all_chronos_jobs:
            if self.subjob_chronos_name in chronos_job:
                delete_from_chronos_by_name(chronos_job, self.cloud)
        self.delete_from_chronos()

    def get_minimum_score(self):
        minimum = 5 if self.method == 'Fisher' else 0.5
        return minimum

    def get_maximum_score(self):
        maximum = 40 if self.method == 'Fisher' else 1
        return maximum

    def get_user_gene_sets(self):
        user_spreadsheet_path = os.path.join(\
            self.userfiles_dir, self.cleaned_gene_set_file_relative_path)
        df_gene_sets = pd.read_csv(user_spreadsheet_path,\
            delimiter='\t', header=0, index_col=0)
        return_val = []
        for column_name in df_gene_sets:
            column = df_gene_sets[column_name]
            gene_ids = column[column > 0].index.tolist()
            return_val.append({'set_id': column_name, 'gene_ids': gene_ids})
        return return_val

    def get_public_gene_set_dict(self, collection_name):
        return_val = {}
        edge_file_path = os.path.join('/networks', \
            self.collection_to_network[collection_name]['path_to_edge'])
        with open(edge_file_path, 'rb') as infile:
            csv_reader = csv.reader(infile, delimiter='\t')
            for row in csv_reader:
                set_id = row[0]
                if set_id not in return_val:
                    return_val[set_id] = set()
                return_val[set_id].add(row[1])
        return return_val

    def get_score_file_paths(self):
        """Returns a list of paths to sorted_by_property_score* files.

        Args:
            None.

        Returns:
            list: A list of paths to sorted_by_property_score* files.

        """
        return_val = []
        results_directories = [os.path.join(self.subjob_dir_path, subdir) \
            for subdir in os.listdir(self.subjob_dir_path) \
            if os.path.isdir(os.path.join(self.subjob_dir_path, subdir))]
        for subdir in results_directories:
            score_files = [os.path.join(subdir, fname) \
                for fname in os.listdir(subdir) \
                if "sorted_by_property_score" in fname]
            if len(score_files) == 1:
                return_val.append(score_files[0])
        return return_val

    def get_collection_name_for_score_file_path(self, score_file_path):
        """Given a score_file_path as found in the list returned by
        get_score_file_paths, returns the name of the collection.

        Args:
            score_file_path (str): The path to the score file.

        Returns:
            str: The name of the collection associated with the score file.

        """
        # TODO could be method
        # collection name is last part of subdir without the trailing
        # "_results"
        dirname = os.path.basename(os.path.dirname(score_file_path))
        return dirname[:-len('_results')]

    def get_set_level_scores(self, user_gene_sets):
        return_val = {}
        # prepare to calculate overlap scores
        user_gene_set_dict = {item['set_id']: set(item['gene_ids']) for \
            item in user_gene_sets}
        # determine threshold
        score_key = 'pval' if self.method == 'Fisher' else 'difference_score'
        minimum = self.get_minimum_score()
        maximum = self.get_maximum_score()
        # iterate over results
        for score_file_path in self.get_score_file_paths():
            collection = self.get_collection_name_for_score_file_path(\
                score_file_path)
            public_gene_set_dict = self.get_public_gene_set_dict(collection)
            with open(score_file_path, 'rb') as csvfile:
                for row in csv.DictReader(csvfile, delimiter='\t'):
                    # enforce ceiling on scores
                    score = min(float(row[score_key]), maximum)
                    if score > minimum:
                        user_gene_set_id = row['user_gene_set']
                        public_gene_set_id = row['property_gene_set']
                        overlap_count = len(\
                            user_gene_set_dict[user_gene_set_id] &
                            public_gene_set_dict[public_gene_set_id])
                        if public_gene_set_id not in return_val:
                            return_val[public_gene_set_id] = {}
                        return_val[public_gene_set_id][user_gene_set_id] = {
                            'shading_score': score,
                            'overlap_count': overlap_count
                        }
        return return_val

    def prepare_zip_file(self):
        """Creates a zip file on disk for later download by the user.

        Args:
            top_genes_by_cluster_file_path (str): The path to the file
                containing top genes per cluster.
            consensus_matrix_file_path (str): The path to the file
                containing consensus clustering scores.
            samples_label_by_cluster_file_path (str): The path to the file
                containing sample labels with their cluster labels.

        Returns:
            None.

        """
        # need the following:
        # 1. readme
        # 2. cleaned matrix
        # 3. gene map
        # 4. interaction network metadata (if using KN)
        # 5. run.yml for each collection
        # 6. collection metadata for each collection
        # 7. pnode map for each collection
        # 8. results for each collection
        zip_path = os.path.join(\
            self.job_dir_path, 'download.zip')
        with ZipFile(zip_path, 'w', ZIP_DEFLATED) as zipout:

            zipout.write(\
                '/zip_readmes/README-GSC.txt', 'README-GSC.txt')

            cleaned_gene_set_file_path = os.path.join(\
                self.userfiles_dir, self.cleaned_gene_set_file_relative_path)
            zipout.write(\
                cleaned_gene_set_file_path, 'clean_gene_set_matrix.txt')

            gene_names_map_path = os.path.join(\
                self.userfiles_dir, self.gene_names_map_relative_path)
            zipout.write(\
                gene_names_map_path, 'gene_map.txt')

            if self.gg_network_metadata_full_path is not None:
                zipout.write(self.gg_network_metadata_full_path, \
                    'interaction_network.metadata')

            for score_file_path in self.get_score_file_paths():
                collection_name = self.get_collection_name_for_score_file_path(\
                    score_file_path)

                zipout.write(self.yml_path_for_collection(collection_name), \
                    os.path.join(collection_name, 'run_params.yml'))

                zipout.write(score_file_path, os.path.join(\
                    collection_name, 'gsc_results.txt'))

                network_info = self.collection_to_network[collection_name]

                pnode_map_file_path = os.path.join('/networks', \
                    network_info['path_to_pnode_map'])
                zipout.write(pnode_map_file_path, os.path.join(\
                    collection_name, 'gene_set_name_map.txt'))

                metadata_file_name = network_info['species_id'] + '.' + \
                    collection_name + '.metadata'
                metadata_file_path = os.path.join('/networks', \
                    network_info['path_to_metadata'])
                zipout.write(metadata_file_path, os.path.join(\
                    collection_name, metadata_file_name))

def get_gene_set_characterization_runners(\
    user_id, job_id, userfiles_dir, project_dir, timeout, cloud, species_id,\
    gene_set_file_id, gene_collections, method, network_name, network_smoothing):
    """Returns a list of ChronosJob instances required to run a GSC job.

    Args:
        user_id (NestId): The user id associated with the job.
        job_id (NestId): The unique identifier the DB assigns to the job.
        userfiles_dir (str): The base directory containing all files for
            all users.
        project_dir (str): The name of the directory containing the files
            associated with the current project.
        timeout (int): The maximum execution time in seconds.
        cloud (str): The cloud name, which must appear as a key in
            nest_py.knoweng.jobs.ChronosJob.cloud_path_dict.
        species_id (str): The species_id to disambiguate networks with
            identical edge_type_names.
        gene_set_file_id (NestId): The _id of the gene-set file in the database.
        gene_collections (list): The name of the public gene collections to
            compare.
        method (str): One of ['Fisher', 'DRaWR'].
        network_name (str): The interaction network to use with
            network-based methods.
        network_smoothing (float): The amount of network smoothing to apply.

    Returns:
        list: A list of ChronosJob instances required to run a GSC job.

    """
    # create the working directory
    job_id_str = job_id.to_slug()
    job_name = "nest_GSC_" + method + '_' + job_id_str
    job_dir_relative_path = os.path.join(project_dir, job_name)
    os.mkdir(os.path.join(userfiles_dir, job_dir_relative_path))

    cleaned_gene_set_file_relative_path = None
    gene_names_map_relative_path = None
    prep_job = None
    # read the first line of the file to determine whether we have a gene-sets
    # matrix or pasted gene list
    gene_set_file_dto = get_file_record(user_id, gene_set_file_id)
    gene_set_file_path = gene_set_file_dto.get_file_path(userfiles_dir)
    with open(gene_set_file_path, 'r') as gene_set_file:
        headers = gene_set_file.readline().strip()
        is_matrix = '\t' in headers # later: or ',' in headers
    if is_matrix:
        prep_job = DataCleanupJob(\
            user_id, job_id, userfiles_dir, timeout, cloud, species_id, \
            gene_set_file_dto, None, None, job_dir_relative_path, \
            PipelineType.GENE_SET_CHARACTERIZATION, None)
        cleaned_gene_set_file_relative_path = \
            get_cleaned_spreadsheet_relative_path(\
                job_dir_relative_path, gene_set_file_dto)
        gene_names_map_relative_path = \
            get_gene_names_map_relative_path(\
                job_dir_relative_path, gene_set_file_dto)
    else:
        prep_job = PastedGeneSetConversionJob(\
            user_id, job_id, userfiles_dir, job_dir_relative_path, timeout,
            cloud, gene_set_file_dto, species_id)
        cleaned_gene_set_file_relative_path = os.path.join(\
            job_dir_relative_path, prep_job.get_output_gene_set_filename())
        gene_names_map_relative_path = os.path.join(\
            job_dir_relative_path, prep_job.get_output_gene_map_filename())

    return [prep_job, GeneSetCharacterizationJob(\
        user_id, job_id, userfiles_dir, job_dir_relative_path, timeout, cloud, \
        species_id, cleaned_gene_set_file_relative_path, \
        gene_names_map_relative_path, gene_collections, method, \
        network_name, network_smoothing, prep_job)]

# TODO data model v1.0
#{
#    job_id: objectid,
#    user_gene_sets: [
#        set_id/name: string,
#        gene_ids: string[]
#    ],
#    set_level_scores: [
#        user_gene_set_id/name: string,
#        public_gene_set_id: string,
#        overlap_count: number, // fisher has overlap_count column; drawr needs...
#        shading_score: number
#    ],
#    gene_level_scores: [
#        gene_id: string,
#        public_gene_set_id: string,
#        shading_score: number,
#        overlap: bool ?
#    ],
#    genes: [ // this should really be its own endpoint
#        gene_id: string,
#        gene_name: string,
#        genecard_summary: string,
#        url or something: string
#    ]
#}
