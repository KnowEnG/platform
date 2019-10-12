"""This module defines a class for running knoweng's gene set characterization jobs."""

import csv
import errno
import logging
import os
from zipfile import ZipFile, ZIP_DEFLATED

import pandas as pd
import yaml

from nest_py.knoweng.jobs.pipeline_job import PipelineJob
from nest_py.knoweng.jobs.db_utils import create_gsc_record, get_file_record, \
    create_file_record
from nest_py.knoweng.jobs.networks import get_merged_network_info
from nest_py.knoweng.jobs.pipelines.pasted_gene_set_conversion import \
    PastedGeneSetConversionJob
from nest_py.knoweng.jobs.pipelines.data_cleanup import \
    DataCleanupJob, PipelineType, get_cleaned_spreadsheet_relative_path, \
    get_gene_names_map_relative_path, create_dummy_mapping, \
    get_gene_names_mapped_and_unmapped_relative_path, map_first_column_of_file,\
    get_dict_from_id_to_name

LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.INFO)

class GeneSetCharacterizationComputeJob(PipelineJob):
    """Subclass of PipelineJob that handles gene set characterization
    for a single gene-set collection."""
    def __init__(self, user_id, job_id, project_id, userfiles_dir, \
        job_dir_relative_path, timeout, cloud, species_id, \
        cleaned_gene_set_file_relative_path, collection, method, network_name, \
        network_smoothing, prep_job):
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
            species_id (str): The species_id to disambiguate networks with
                identical edge_type_names.
            cleaned_gene_set_file_relative_path (str): The relative path from
                userfiles_dir to the cleaned gene-set file.
            collection (str): The name of the public gene-set collection to
                compare.
            method (str): One of ['Fisher', 'DRaWR'].
            network_name (str): The interaction network to use with
                network-based methods.
            network_smoothing (float): The amount of network smoothing to apply.
            prep_job (PipelineJob): The DataCleanupJob or
                PastedGeneSetConversionJob that will prepare the data for this
                job.

        Returns:
            None: None.

        """
        job_name = 'nest-gsc-' + job_id.to_slug().lower() + '-' + \
            collection.lower().replace('_', '')
        LOGGER.debug(job_name + '.__init__')
        self.prep_job = prep_job
        self.cleaned_gene_set_file_relative_path = \
            cleaned_gene_set_file_relative_path

        networks = get_merged_network_info('/networks/')

        self.job_dir_path = os.path.join(userfiles_dir, job_dir_relative_path)

        # create dummy mapping, since our input file has already been cleaned
        # don't actually create the file until `start` call, because gene-name
        # mapping may not have produced cleaned_gene_set_file_relative_path yet
        self.dummy_map_name = 'dummy_map.tsv'

        docker_image = 'knowengdev/geneset_characterization_pipeline:01_29_2019'

        # create yaml files
        self.run_data = {
            'spreadsheet_name_full_path': '../../../' + \
                self.cleaned_gene_set_file_relative_path,
            'gene_names_map': './' + self.dummy_map_name,
            # also see image tag in get_command--that one will be removed soon
            'docker_image': docker_image
        }
        if method == 'Fisher':
            self.run_data['method'] = 'fisher'
            # For max_ram_mb, 1000 worked for default Fisher on knowdev instance
            # NOTE: We set a minimum of 2500MB to keep the Kubernetes scheduler
            # happy
            limit_ram_mb = 2500
            limit_num_cpus = 2
            self.run_data['max_cpu'] = limit_num_cpus
        elif method == 'DRaWR':
            self.run_data['method'] = 'DRaWR'
            # For max_ram_mb, 2000 was needed for default DRaWR on knowdev
            # instance
            # NOTE: 6000+ is required for "STRING Text Mining from Abstracts" to
            # complete on all public gene sets
            limit_ram_mb = 6000
            limit_num_cpus = 2
            self.run_data['max_cpu'] = limit_num_cpus
            self.run_data['rwr_max_iterations'] = 500
            self.run_data['rwr_convergence_tolerence'] = 1.0e-4
            self.run_data['rwr_restart_probability'] = \
                float(network_smoothing)/100
            gg_info = [net for net in networks if \
                net['species_id'] == species_id and \
                net['edge_type_name'] == network_name][0]
            self.run_data['gg_network_name_full_path'] = \
                '../../../../networks/' + gg_info['path_to_edge']
        else:
            raise ValueError('Unknown method ' + method)

        # create a mapping from collection name to network info
        network_info = [net for net in networks if \
            net['species_id'] == species_id and \
            net['edge_type_name'] == collection][0]

        results_directory_relative_path = './' + collection + '_results'
        self.run_data['results_directory'] = results_directory_relative_path
        self.run_data['pg_network_name_full_path'] = '../../../../networks/' + \
            network_info['path_to_edge']

        results_directory = os.path.join(\
            self.job_dir_path, results_directory_relative_path)

        # Ensure that results_directory exists
        try:
            os.makedirs(results_directory)
        except OSError as exc:
            if exc.errno == errno.EEXIST and os.path.isdir(results_directory):
                pass
            else:
                raise

        self.yml_path = self.yml_path_for_collection(collection)
        with open(self.yml_path, 'wb') as outfile:
            yaml.safe_dump(self.run_data, outfile, default_flow_style=False)

        super(GeneSetCharacterizationComputeJob, self).__init__(\
            user_id, job_id, project_id, userfiles_dir, job_dir_relative_path,\
            job_name, timeout, cloud, docker_image, limit_num_cpus,\
            limit_ram_mb)

    def yml_path_for_collection(self, collection):
        """Returns the yml file path for a collection's subjob.

        Args:
            collection (str): The name of the collection.

        Returns:
            str: The path to the yml file for the collection's subjob.

        """
        return os.path.join(self.job_dir_path, collection + '.yml')

    def start(self):
        dummy_out_path = os.path.join(self.job_dir_path, self.dummy_map_name)
        if not os.path.isfile(dummy_out_path):
            dummy_in_path = os.path.join(\
                self.userfiles_dir, self.cleaned_gene_set_file_relative_path)
            create_dummy_mapping(dummy_in_path, dummy_out_path)
        super(GeneSetCharacterizationComputeJob, self).start()

    def get_command(self):
        """Returns the docker command for gene_set_characterization."""
        LOGGER.debug(self.job_name + '.get_command')
        cd_path = os.path.join(PipelineJob.get_cloud_path(self.cloud),\
            'userfiles', self.job_dir_relative_path)
        yml_filename = os.path.basename(self.yml_path)
        return 'date && cd ' + cd_path + \
            ' && python3 /home/src/geneset_characterization.py' + \
            ' -run_directory ./' + \
            ' -run_file ' + yml_filename + \
            ' && date;'

    def is_ready(self):
        return_val = self.prep_job.is_done()
        LOGGER.debug(self.job_name + '.is_ready? ' + str(return_val))
        return return_val

    def is_done(self):
        # Build up the absolute path of the results_directory
        results_directory_relative_path = self.run_data['results_directory']
        results_directory = os.path.join(\
            self.job_dir_path, results_directory_relative_path)

        # Check for existence of droplist file in the job's results directory
        # droplist file is last to be written
        score_files = [fname for fname in os.listdir(results_directory) \
            if "_droplist" in fname]

        return_val = len(score_files) == 1
        LOGGER.debug(self.job_name + '.is_done? ' + str(return_val))
        return return_val

    def on_done(self):
        """Deletes self from executor.

            Returns:
                None: None.

        """
        LOGGER.debug(self.job_name + '.on_done')
        self.delete_job_record()

class GeneSetCharacterizationWrapupJob(object):
    """Handles gene set characterization job cleanup."""
    def __init__(self, user_id, job_id, project_id, userfiles_dir, \
        job_dir_relative_path, subjob_dir_relative_path, \
        species_id, cleaned_gene_set_file_relative_path, \
        gene_names_map_relative_path, \
        gene_names_mapped_and_unmapped_relative_path, gene_collections, \
        method, network_name, prep_jobs):
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
            subjob_dir_relative_path (str): The relative path from
                userfiles_dir to the directory containing the output
                files from the GSCComputeJobs, which must already exist.
            species_id (str): The species_id to disambiguate networks with
                identical edge_type_names.
            cleaned_gene_set_file_relative_path (str): The relative path from
                userfiles_dir to the cleaned gene-set file.
            gene_names_map_relative_path (str): The relative path from
                userfiles_dir to the gene-names map.
            gene_names_mapped_and_unmapped_relative_path (str): The relative
                path from userfiles_dir to the file containing the gene names,
                mapped and unmapped.
            gene_collections (list): The name of the public gene collections to
                compare.
            method (str): One of ['Fisher', 'DRaWR'].
            network_name (str): The interaction network to use with
                network-based methods.
            prep_jobs ([PipelineJob]): The runners that preceeded this one in
                execution; i.e., one of either DataCleanupJob or
                PastedGeneSetConversionJob, and one
                GeneSetCharacterizationComputeJob per collection.

        Returns:
            None: None.

        """
        self.job_name = 'nest-gsc-' + job_id.to_slug().lower() + '-wrapup'
        LOGGER.debug(self.job_name + '.__init__')
        self.started = False

        self.cleaned_gene_set_file_relative_path = \
            cleaned_gene_set_file_relative_path
        self.gene_names_map_relative_path = gene_names_map_relative_path
        self.gene_names_mapped_and_unmapped_relative_path = \
            gene_names_mapped_and_unmapped_relative_path
        self.method = method
        self.userfiles_dir = userfiles_dir
        self.user_id = user_id
        self.job_id = job_id
        self.project_id = project_id

        self.prep_jobs = prep_jobs

        networks = get_merged_network_info('/networks/')

        self.job_dir_path = os.path.join(userfiles_dir, job_dir_relative_path)
        self.subjob_dir_path = os.path.join(\
            userfiles_dir, subjob_dir_relative_path)

        # Provide a path to the appropriate network file, or don't
        self.gg_network_metadata_full_path = None
        if method == 'DRaWR':
            gg_info = [net for net in networks if \
                net['species_id'] == species_id and \
                net['edge_type_name'] == network_name][0]
            self.gg_network_metadata_full_path = '../../../../networks/' + \
                gg_info['path_to_metadata']

        # create a mapping from collection name to network info
        self.collection_to_network = {}
        for collection in gene_collections:
            network_info = [net for net in networks if \
                net['species_id'] == species_id and \
                net['edge_type_name'] == collection][0]
            self.collection_to_network[collection] = network_info

    def is_started(self):
        return self.started

    def yml_path_for_collection(self, collection):
        """Returns the yml file path for a collection's subjob.

        Args:
            collection (str): The name of the collection.

        Returns:
            str: The path to the yml file for the collection's subjob.

        """
        return os.path.join(self.subjob_dir_path, collection + '.yml')

    def is_failed(self):
        LOGGER.debug(self.job_name + '.is_failed? False')
        return False

    def is_ready(self):
        """Processes scores, loads data to database, prepares zip file, and
        deletes self and children from the executor.

            Returns:
                bool: True if the prep jobs have finished and all wrapup work
                    was subsequently completed, else False.

        """
        # Verify that all prep_jobs are done
        for prep_job in self.prep_jobs:
            if not prep_job.is_done():
                LOGGER.debug(self.job_name + '.is_ready? False')
                return False

        LOGGER.debug(self.job_name + '.is_ready? True')

        # Since Wrapup executes locally (no container), just do its work here
        user_gene_sets = self.get_user_gene_sets()
        set_level_scores = self.get_set_level_scores(user_gene_sets)

        # we'll need this in preparing output files and for later gene-level
        # drilldown
        gnm_path = os.path.join(self.userfiles_dir,\
                self.gene_names_map_relative_path)
        gene_id_to_name = get_dict_from_id_to_name(gnm_path, None)

        create_gsc_record(self.user_id, self.job_id, user_gene_sets, \
            set_level_scores, self.get_minimum_score())
        output_file_info = self.prepare_output_files(gene_id_to_name)
        self.capture_files_in_db(output_file_info)
        self.capture_files_in_zip(output_file_info)

        # Run locally: manually mark job as "done"
        self.started = True
        return True

    def is_done(self):
        LOGGER.debug(self.job_name + '.is_done? ' + str(self.started))
        return self.started

    def on_done(self):
        """Does nothing, because the real work for this locally-executed job
        is done in is_ready.

        Returns:
            None: None.

        """
        LOGGER.info(self.job_name + '.on_done')

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
        return self.get_subjob_file_paths_by_substring(\
            "sorted_by_property_score")

    def get_droplist_paths(self):
        """Returns a list of paths to droplist files.

        Args:
            None.

        Returns:
            list: A list of paths to droplist files.

        """
        return self.get_subjob_file_paths_by_substring("droplist")

    def get_subjob_file_paths_by_substring(self, substring):
        """Returns a list of paths to output files from the subjobs whose
        filenames include the given substring.

        Args:
            substring (str): The substring to match in subjob output filenames.

        Returns:
            list: A list of paths to matching files.

        """
        return_val = []
        results_directories = [os.path.join(self.subjob_dir_path, subdir) \
            for subdir in os.listdir(self.subjob_dir_path) \
            if os.path.isdir(os.path.join(self.subjob_dir_path, subdir))]
        for subdir in results_directories:
            score_files = [os.path.join(subdir, fname) \
                for fname in os.listdir(subdir) \
                if substring in fname]
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

    def prepare_output_files(self, gene_id_to_name):
        """Transforms output files in preparation for capture as new file
        records in the DB and/or as members of the download zip.

        Args:
            gene_id_to_name (dict): A dictionary from gene id to gene name.

        Returns:
           list: A list of dicts. Each dict represents a single output file and
               contains keys 'path', 'name', 'in_db', and 'in_zip'.

        """
        output_file_info = []

        cleaned_gene_set_file_path = os.path.join(\
            self.userfiles_dir, self.cleaned_gene_set_file_relative_path)
        transformed_gene_set_file_path = \
            cleaned_gene_set_file_path + ".transformed"
        map_first_column_of_file(\
            cleaned_gene_set_file_path, \
            transformed_gene_set_file_path, \
            gene_id_to_name)
        output_file_info.append({
            'path': transformed_gene_set_file_path,
            'name': 'clean_gene_set_matrix.txt',
            'in_db': False,
            'in_zip': True
        })

        output_file_info.append({
            'path': '/pipeline_readmes/README-GSC.md',
            'name': 'README-GSC.md',
            'in_db': False,
            'in_zip': True
        })
        cleanup_job = [job for job in self.prep_jobs if isinstance(job, \
            (DataCleanupJob, PastedGeneSetConversionJob))][0]
        output_file_info.append({
            'path': cleanup_job.get_run_file_path(),
            'name': 'run_cleanup_params.yml',
            'in_db': False,
            'in_zip': True
        })
        gene_names_mapped_and_unmapped_path = os.path.join(\
            self.userfiles_dir,
            self.gene_names_mapped_and_unmapped_relative_path)
        output_file_info.append({
            'path': gene_names_mapped_and_unmapped_path,
            'name': 'gene_map.txt',
            'in_db': False,
            'in_zip': True
        })
        if self.gg_network_metadata_full_path is not None:
            output_file_info.append({
                'path': self.gg_network_metadata_full_path,
                'name': 'interaction_network.metadata',
                'in_db': False,
                'in_zip': True
            })

        # combined_results.txt will contain the results of all subjobs
        # combined_run_params.yml will contain run_params from all subjobs
        # combined_metadata.txt will contain the metadata from all PG networks
        # combined_droplist.txt will contain the droplists from all subjobs
        combined_results_path = os.path.join(\
            self.job_dir_path, 'combined_results.txt')
        combined_run_params_path = os.path.join(\
            self.job_dir_path, 'combined_run_params.yml')
        combined_metadata_path = os.path.join(\
            self.job_dir_path, 'combined_metadata.txt')
        combined_droplist_path = os.path.join(\
            self.job_dir_path, 'combined_droplist.txt')

        results_needs_header = True
        droplist_needs_header = True

        droplist_paths = self.get_droplist_paths()

        with open(combined_results_path, 'w') as results_out, \
                open(combined_run_params_path, 'w') as params_out, \
                open(combined_metadata_path, 'w') as metadata_out, \
                open(combined_droplist_path, 'w') as droplist_out:

            for score_file_path in self.get_score_file_paths():

                # gather collection info
                collection_name = self.get_collection_name_for_score_file_path(\
                    score_file_path)
                network_info = self.collection_to_network[collection_name]

                # load gene collection aliases and descriptions
                pnode_map_file_path = os.path.join('/networks', \
                    network_info['path_to_pnode_map'])
                collection_id_to_alias = {}
                collection_id_to_description = {}
                with open(pnode_map_file_path, 'r') as infile:
                    for line in infile:
                        pieces = line.rstrip().split("\t")
                        collection_id_to_alias[pieces[0]] = pieces[3]
                        # because fifth column is the last, if it's empty,
                        # the rstrip above will remove it entirely
                        collection_id_to_description[pieces[0]] = \
                            pieces[4] if len(pieces) >= 5 else ''
                # add to results
                with open(score_file_path, 'r') as results_in:
                    for num, line in enumerate(results_in):
                        pieces = line.rstrip().split("\t")
                        if num == 0:
                            if results_needs_header:
                                score_label = "negative_log10_pvalue" if \
                                    self.method == 'Fisher' else pieces[2]
                                out_array = [pieces[0], "property_gene_set_id",\
                                    "property_gene_set_alias",\
                                    "property_gene_set_description",\
                                    "collection", score_label] + \
                                    pieces[3:]
                                results_out.write("\t".join(out_array) + "\n")
                                results_needs_header = False
                            else:
                                pass # skip header
                        else:
                            gsid = pieces[1]
                            alias = collection_id_to_alias[gsid]
                            description = collection_id_to_description[gsid]
                            out_array = [pieces[0], gsid, alias, description,\
                                collection_name] + pieces[2:]
                            results_out.write("\t".join(out_array) + "\n")

                yml_separator = "---\n#\n# COLLECTION: " + collection_name + \
                    "\n#\n"

                # add to params
                params_out.write(yml_separator)
                run_params_path = self.yml_path_for_collection(collection_name)
                with open(run_params_path, 'r') as params_in:
                    for line in params_in:
                        params_out.write(line)

                # add to metadata
                metadata_out.write(yml_separator)
                metadata_file_path = os.path.join('/networks', \
                    network_info['path_to_metadata'])
                with open(metadata_file_path, 'r') as metadata_in:
                    for line in metadata_in:
                        metadata_out.write(line)

                # add to droplists
                droplist_paths_matches = [dlp for dlp in droplist_paths \
                    if collection_name in dlp]
                if len(droplist_paths_matches) == 1:
                    with open(droplist_paths_matches[0], 'r') as droplist_in:
                        for num, line in enumerate(droplist_in):
                            gene_id = line.rstrip()
                            if num == 0:
                                if droplist_needs_header:
                                    droplist_out.write(\
                                        "collection\tgene_name\tgene_id\n")
                                    droplist_needs_header = False
                                else:
                                    pass # skip header
                            elif gene_id in gene_id_to_name:
                                droplist_out.write(\
                                    collection_name + "\t" + \
                                    gene_id_to_name[gene_id] + "\t" + \
                                    gene_id + "\n")
                            else:
                                # gene_id not found in gene_id_to_name means
                                # this is part of the universe introduced by
                                # pasted gene set conversion. Charles said
                                # exclude the universe-only genes from the
                                # downloaded droplist.
                                pass

            output_file_info.append({
                'path': combined_results_path,
                'name': 'gsc_results.txt',
                'in_db': True,
                'in_zip': True
            })
            output_file_info.append({
                'path': combined_run_params_path,
                'name': 'run_params.yml',
                'in_db': False,
                'in_zip': True
            })
            output_file_info.append({
                'path': combined_metadata_path,
                'name': 'property_networks.metadata',
                'in_db': False,
                'in_zip': True
            })
            output_file_info.append({
                'path': combined_droplist_path,
                'name': 'dropped_genes.txt',
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

def get_gene_set_characterization_runners(\
    user_id, job_id, project_id, userfiles_dir, project_dir, timeout, cloud,\
    species_id, gene_set_file_id, gene_collections, method, network_name,\
    network_smoothing):
    """Returns a list of PipelineJob instances required to run a GSC job.

    Args:
        user_id (NestId): The user id associated with the job.
        job_id (NestId): The unique identifier the DB assigns to the job.
        project_id (NestId): The project id associated with the job.
        userfiles_dir (str): The base directory containing all files for
            all users.
        project_dir (str): The name of the directory containing the files
            associated with the current project.
        timeout (int): The maximum execution time in seconds.
        cloud (str): The cloud name, which must appear as a key in
            your executor's cloud_path_dict.
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
        list: A list of PipelineJob instances required to run a GSC job.

    """
    # create the working directory
    job_name = "nest-gsc-" + method.lower() + '-' + job_id.to_slug().lower()
    job_dir_relative_path = os.path.join(project_dir, job_name)
    job_dir_path = os.path.join(userfiles_dir, job_dir_relative_path)
    LOGGER.info('Creating directory: ' + job_dir_path)
    os.mkdir(job_dir_path)

    cleaned_gene_set_file_relative_path = None
    gene_names_map_relative_path = None
    gene_names_mapped_and_unmapped_relative_path = None
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
            user_id, job_id, project_id, userfiles_dir, timeout, cloud,\
            species_id, gene_set_file_dto, None, None, job_dir_relative_path,\
            PipelineType.GENE_SET_CHARACTERIZATION, None, None)
        cleaned_gene_set_file_relative_path = \
            get_cleaned_spreadsheet_relative_path(\
                job_dir_relative_path, gene_set_file_dto)
        gene_names_map_relative_path = \
            get_gene_names_map_relative_path(\
                job_dir_relative_path, gene_set_file_dto)
    else:
        prep_job = PastedGeneSetConversionJob(\
            user_id, job_id, project_id, userfiles_dir, job_dir_relative_path,\
            timeout, cloud, gene_set_file_dto, species_id)
        cleaned_gene_set_file_relative_path = os.path.join(\
            job_dir_relative_path, prep_job.get_output_gene_set_filename())
        gene_names_map_relative_path = os.path.join(\
            job_dir_relative_path, prep_job.get_output_gene_map_filename())
    gene_names_mapped_and_unmapped_relative_path = \
        get_gene_names_mapped_and_unmapped_relative_path(\
            job_dir_relative_path, gene_set_file_dto)

    # Create our subjobs directory here
    subjob_dir_name = 'subjobs'
    subjob_dir_path = os.path.join(job_dir_path, subjob_dir_name)
    LOGGER.info('Creating directory: ' + subjob_dir_path)
    os.mkdir(subjob_dir_path)

    subjob_dir_relative_path = os.path.join(job_dir_relative_path, subjob_dir_name)

    # Starting with our prep_job, build up the necessary set of PipelineJobs to run
    jobs_to_run = [prep_job]
    for collection in gene_collections:
        jobs_to_run.append(GeneSetCharacterizationComputeJob(\
            user_id, job_id, project_id, userfiles_dir, \
            subjob_dir_relative_path, timeout, cloud, species_id, \
            cleaned_gene_set_file_relative_path, collection, method, \
            network_name, network_smoothing, prep_job))

    jobs_to_run.append(GeneSetCharacterizationWrapupJob(\
        user_id, job_id, project_id, userfiles_dir, job_dir_relative_path, \
        subjob_dir_relative_path, species_id, \
        cleaned_gene_set_file_relative_path, gene_names_map_relative_path, \
        gene_names_mapped_and_unmapped_relative_path, gene_collections, \
        method, network_name, list(jobs_to_run)))

    return jobs_to_run

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
