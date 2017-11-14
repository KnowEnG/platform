"""This module defines a class for running knoweng's gene prioritization jobs."""

### Summary of paths and docker mounts for AWS (TODO: generalize across hosts and pipelines) ###
# on the host:
#
# /mnt/storage/interface/   <-- mounted to pipeline's docker container
#
# /mnt/storage/interface/networks/   <-- contains network files in tree of subdirectories
#
# /mnt/storage/interface/userfiles/projectid/jobs/jobid/   <-- contains yml file
#
# /mnt/storage/interface/userfiles/projectid/jobs/jobid/results/   <-- contains outputs
#
# /mnt/storage/interface/userfiles/projectid/files/fileid   <-- the user's features file
# /mnt/storage/interface/userfiles/projectid/files/file2id   <-- the user's response file
#
#
# in the container:
#
# /home/run_dir/ can map to the host's /mnt/storage/interface/
#
#
# calling the script:
#
# -run_directory can be /home/run_dir/userfiles/projectid/jobs/jobid/
# -run_file can be the name of a yml file in that directory
#
#
# in the yml file:
#
# (working directory will be /home/run_dir/userfiles/projectid/jobid/)
# results_directory can be ./results/
# network file paths will look like ../../../networks/...
# spreadsheet files paths will look like ../fileid

import csv
import os
from zipfile import ZipFile, ZIP_DEFLATED

import yaml

from nest_py.knoweng.jobs.chronos_job import ChronosJob
from nest_py.knoweng.jobs.db_utils import create_gp_record, get_file_record
from nest_py.knoweng.jobs.networks import get_merged_network_info
from nest_py.knoweng.jobs.data_cleanup import \
    DataCleanupJob, PipelineType, CorrelationMeasure, \
    get_cleaned_spreadsheet_relative_path, get_gene_names_map_relative_path, \
    get_dict_from_id_to_name

class GenePrioritizationJob(ChronosJob):
    """Subclass of ChronosJob that handles gene prioritization jobs."""
    def __init__(self, user_id, job_id, userfiles_dir, job_dir_relative_path,
                 timeout, cloud, species_id, features_file_relative_path,
                 gene_names_map_relative_path, response_file_relative_path,
                 correlation_method, use_network, network_name,
                 network_influence, num_response_correlated_genes,
                 use_bootstrapping, num_bootstraps, bootstrap_sample_percent,
                 prep_job):
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
            features_file_relative_path (str): The relative path from the
                userfiles_dir to the features file.
            gene_names_map_relative_path (str): The relative path from the
                userfiles_dir to the gene-name map.
            response_file_relative_path (str): The relative path from the
                userfiles_dir to the response file.
            correlation_method (str): One of ['pearson', 't_test'].
            use_network (bool): Whether to use the knowledge network.
            network_name (str): The network to use when use_network is True.
            network_influence (float): The amount of network influence to use.
            num_response_correlated_genes (int): The number of top genes from
                the correlation analysis to carry over to the network analysis.
            use_bootstrapping (bool): Whether to use bootstrapping.
            num_bootstraps (int): The number of bootstraps to run.
            bootstrap_sample_percent (float): The percentage of columns to use
                per bootstrap.
            prep_job (DataCleanupJob): The job that prepares the inputs.

        Returns:
            None: None.

        """
        self.features_file_relative_path = features_file_relative_path
        self.gene_names_map_relative_path = gene_names_map_relative_path
        self.response_file_relative_path = response_file_relative_path
        self.prep_job = prep_job

        self.job_dir_path = os.path.join(userfiles_dir, job_dir_relative_path)

        self.results_dir_path = os.path.join(self.job_dir_path, 'results')
        os.mkdir(self.results_dir_path)

        # create yaml file
        run_data = {
            'correlation_measure': correlation_method,
            'spreadsheet_name_full_path': '../../' + features_file_relative_path,
            'phenotype_name_full_path': '../../' + response_file_relative_path,
            'results_directory': './results',
            'drop_method': 'drop_NA'
        }

        if use_network:
            networks = get_merged_network_info('/networks/')
            network_info = [net for net in networks if \
                net['species_id'] == species_id and \
                net['edge_type_name'] == network_name][0]
            run_data['gg_network_name_full_path'] = '../../../networks/' + \
                network_info['path_to_edge']
            self.gg_network_metadata_full_path = '../../../networks/' + \
                network_info['path_to_metadata']

            run_data['rwr_max_iterations'] = 100
            run_data['rwr_convergence_tolerence'] = 1.0e-4
            run_data['rwr_restart_probability'] = \
                1 - float(network_influence)/100
            run_data['top_beta_of_sort'] = num_response_correlated_genes
        else:
            run_data['top_beta_of_sort'] = 100 # TODO Nahil says we need this
            self.gg_network_metadata_full_path = None
        if use_bootstrapping:
            run_data['number_of_bootstraps'] = num_bootstraps
            run_data['rows_sampling_fraction'] = 1.0
            run_data['cols_sampling_fraction'] = \
                float(bootstrap_sample_percent)/100
        if use_network and use_bootstrapping:
            run_data['method'] = 'bootstrap_net_correlation'
        elif use_network and not use_bootstrapping:
            run_data['method'] = 'net_correlation'
        elif not use_network and use_bootstrapping:
            run_data['method'] = 'bootstrap_correlation'
        else:
            run_data['method'] = 'correlation'

        self.yml_path = os.path.join(self.job_dir_path, 'run.yml')
        with open(self.yml_path, 'wb') as outfile:
            yaml.safe_dump(run_data, outfile, default_flow_style=False)

        job_name = 'nest_GP_' + correlation_method + '_' + job_id.to_slug()
        super(GenePrioritizationJob, self).__init__(\
            user_id, job_id, userfiles_dir, job_dir_relative_path, \
            job_name, timeout, cloud,
            'knowengdev/gene_prioritization_pipeline:07_26_2017', 8, 15000)

    def get_command(self):
        """Returns the docker command for gene_prioritization."""
        return 'date && cd ' + \
            os.path.join(ChronosJob.cloud_path_dict[self.cloud], \
                'userfiles', self.job_dir_relative_path) + \
            ' && python3 /home/src/gene_prioritization.py ' + \
            ' -run_directory ./' + \
            ' -run_file run.yml' + \
            ' && date;'

    def is_ready(self):
        """Returns true iff preprocessing is done."""
        return self.prep_job.is_done()

    def is_done(self):
        """Returns true iff all of the files have been created."""
        return_val = False
        for name in os.listdir(self.results_dir_path):
            if name.startswith('top_genes_per_phenotype'):
                return_val = True
        return return_val

    def on_done(self):
        """Processes scores, loads data to database, prepares zip file, and
        deletes self from Chronos.

            Returns:
                None: None.

        """
        scores = {}
        # TODO KNOW-153
        complete_gene_id_to_name = get_dict_from_id_to_name(\
            os.path.join(self.userfiles_dir, self.gene_names_map_relative_path))
        seen_gene_id_to_name = {}
        for name in self.get_response_files():
            csvfile_path = os.path.join(self.results_dir_path, name)
            with open(csvfile_path, 'rb') as csvfile:
                # TODO FIXME read more top scores:
                # 1. to support threshold beyond 100
                # 2. to display actual values when included by union
                count = 0
                for row in csv.DictReader(csvfile, delimiter='\t'):
                    resp = row['Response']
                    if resp not in scores:
                        scores[resp] = {}
                    gene_id = row['Gene_ENSEMBL_ID']
                    scores[resp][gene_id] = \
                        float(row['visualization_score'])
                    seen_gene_id_to_name[gene_id] = \
                        complete_gene_id_to_name.get(gene_id, gene_id)
                    count += 1
                    if count > 100:
                        break
        create_gp_record(self.user_id, self.job_id, scores, 0,\
            seen_gene_id_to_name)
        self.prepare_zip_file()
        self.delete_from_chronos()

    def get_response_files(self):
        return [f for f in os.listdir(self.results_dir_path) \
            if not f.startswith('ranked_genes_per_phenotype') and \
            not f.startswith('top_genes_per_phenotype') and \
            os.path.isfile(os.path.join(self.results_dir_path, f))]

    def prepare_zip_file(self):
        """Creates a zip file on disk for later download by the user.

        Args:
            None.

        Returns:
            None.

        """
        # need the following:
        # 1. readme
        # 2. cleaned features file
        # 3. gene map
        # 4. clean response file
        # 5. run.yml
        # 6. combined viz scores files
        # 7. all top_genes_per_phenotype* files
        # 8. network metadata
        zip_path = os.path.join(\
            self.job_dir_path, 'download.zip')
        with ZipFile(zip_path, 'w', ZIP_DEFLATED) as zipout:

            zipout.write(\
                '/zip_readmes/README-GP.txt', 'README-GP.txt')

            cleaned_features_path = os.path.join(\
                self.userfiles_dir, self.features_file_relative_path)
            zipout.write(\
                cleaned_features_path, 'clean_genomic_matrix.txt')

            gene_names_map_path = os.path.join(\
                self.userfiles_dir, self.gene_names_map_relative_path)
            zipout.write(\
                gene_names_map_path, 'gene_map.txt')

            cleaned_response_path = os.path.join(\
                self.userfiles_dir, self.response_file_relative_path)
            zipout.write(\
                cleaned_response_path, 'clean_phenotypic_matrix.txt')

            zipout.write(\
                self.yml_path, 'run_params.yml')

            # combine viz files
            combined_viz_path = os.path.join(self.job_dir_path, \
                'combined_viz.tsv')
            with open(combined_viz_path, 'w') as combo:
                for fidx, fname in enumerate(sorted(self.get_response_files())):
                    fpath = os.path.join(self.results_dir_path, fname)
                    with open(fpath, 'r') as vizfile:
                        for lidx, line in enumerate(vizfile):
                            if lidx == 0 and fidx > 0:
                                # only print the column labels once
                                pass
                            else:
                                combo.write(line)
            zipout.write(combined_viz_path, 'genes_ranked_per_phenotype.txt')

            top_genes_files = [f for f in os.listdir(self.results_dir_path) \
                if f.startswith('top_genes_per_phenotype')]
            if len(top_genes_files) == 1:
                top_genes_file_path = os.path.join(\
                    self.results_dir_path, top_genes_files[0])
                zipout.write(\
                    top_genes_file_path, 'top_genes_per_phenotype_matrix.txt')

            if self.gg_network_metadata_full_path is not None:
                zipout.write(self.gg_network_metadata_full_path, \
                    'interaction_network.metadata')

def get_gene_prioritization_runners(\
    user_id, job_id, userfiles_dir, project_dir, timeout, cloud, species_id,\
    features_file_id, response_file_id, correlation_method, use_network,\
    network_name, network_influence, num_response_correlated_genes,\
    use_bootstrapping, num_bootstraps, bootstrap_sample_percent):
    """Returns a list of ChronosJob instances required to run a GP job.

    Args:
        user_id (NestId): The user id associated with the job.
        job_id (NestId): The unique identifier Eve/Mongo assigns to the job.
        userfiles_dir (str): The base directory containing all files for
            all users.
        project_dir (str): The name of the directory containing the files
            associated with the current project.
        timeout (int): The maximum execution time in seconds.
        cloud (str): The cloud name, which must appear as a key in
            nest_py.knoweng.jobs.ChronosJob.cloud_path_dict.
        species_id (str): The species_id to disambiguate networks with
            identical edge_type_names.
        features_file_id (NestId): The _id of the features file in the database.
        response_file_id (NestId): The _id of the response file in the database.
        correlation_method (str): One of ['pearson', 't_test'].
        use_network (bool): Whether to use the knowledge network.
        network_name (str): The network to use when use_network is True.
        network_influence (float): The amount of network influence to use.
        num_response_correlated_genes (int): The number of top genes from
            the correlation analysis to carry over to the network analysis.
        use_bootstrapping (bool): Whether to use bootstrapping.
        num_bootstraps (int): The number of bootstraps to run.
        bootstrap_sample_percent (float): The percentage of columns to use
            per bootstrap.

    Returns:
        list: A list of ChronosJob instances required to run a GP job.

    """

    job_name = "nest_GP_" + correlation_method + '_' + job_id.to_slug()
    job_dir_relative_path = os.path.join(project_dir, job_name)
    os.mkdir(os.path.join(userfiles_dir, job_dir_relative_path))

    features_file_dto = get_file_record(user_id, features_file_id)
    cleaned_features_file_relative_path = \
        get_cleaned_spreadsheet_relative_path(\
            job_dir_relative_path, features_file_dto)

    gene_names_map_relative_path = \
        get_gene_names_map_relative_path(\
            job_dir_relative_path, features_file_dto)

    response_file_dto = get_file_record(user_id, response_file_id)
    response_file_relative_path = \
        get_cleaned_spreadsheet_relative_path(\
            job_dir_relative_path, response_file_dto)

    dc_method = None
    if correlation_method == 't_test':
        dc_method = CorrelationMeasure.T_TEST
    elif correlation_method == 'pearson':
        dc_method = CorrelationMeasure.PEARSON
    else:
        # TODO error
        pass
    prep_job = DataCleanupJob(\
        user_id, job_id, userfiles_dir, timeout, cloud, species_id,
        features_file_dto, response_file_dto, None,
        job_dir_relative_path, PipelineType.GENE_PRIORITIZATION, dc_method)
    return [
        prep_job,
        GenePrioritizationJob(\
            user_id, job_id, userfiles_dir, job_dir_relative_path, timeout,
            cloud, species_id, cleaned_features_file_relative_path,
            gene_names_map_relative_path, response_file_relative_path,
            correlation_method, use_network, network_name, network_influence,
            num_response_correlated_genes, use_bootstrapping, num_bootstraps,
            bootstrap_sample_percent, prep_job)
    ]
