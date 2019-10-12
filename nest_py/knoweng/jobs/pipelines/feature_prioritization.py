"""This module defines a class for running knoweng's feature prioritization jobs."""

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
import logging
import os
from zipfile import ZipFile, ZIP_DEFLATED

import yaml

from nest_py.knoweng.jobs.pipeline_job import PipelineJob
from nest_py.knoweng.jobs.db_utils import create_fp_record, get_file_record,\
    create_file_record
from nest_py.knoweng.jobs.networks import get_merged_network_info
from nest_py.knoweng.jobs.pipelines.data_cleanup import \
    DataCleanupJob, PipelineType, CorrelationMeasure, MissingValuesMethod,\
    get_cleaned_spreadsheet_relative_path, get_gene_names_map_relative_path,\
    get_gene_names_mapped_and_unmapped_relative_path, map_first_column_of_file,\
    get_dict_from_id_to_name

LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.INFO)

class FeaturePrioritizationJob(PipelineJob):
    """Subclass of PipelineJob that handles feature prioritization jobs."""
    def __init__(self, user_id, job_id, project_id, userfiles_dir,
                 job_dir_relative_path, timeout, cloud,
                 features_file_relative_path, gene_names_map_relative_path,
                 gene_names_mapped_and_unmapped_relative_path,
                 response_file_relative_path, correlation_method,
                 gg_network_name_full_path, gg_network_node_map_full_path,
                 gg_network_metadata_full_path, network_influence,
                 num_response_correlated_features, num_exported_features,
                 use_bootstrapping, num_bootstraps, bootstrap_sample_percent,
                 prep_job):
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
            features_file_relative_path (str): The relative path from the
                userfiles_dir to the features file.
            gene_names_map_relative_path (str): The relative path from the
                userfiles_dir to the gene-name map, or None if no gene-name
                mapping will be done.
            gene_names_mapped_and_unmapped_relative_path (str): The relative
                path from the userfiles_dir to the file of gene names, mapped
                and unmapped, or None if no gene-name mapping will be done.
            response_file_relative_path (str): The relative path from the
                userfiles_dir to the response file.
            correlation_method (str): One of ['pearson', 't_test', 'edgeR'].
            gg_network_name_full_path (str): The path to the gene-gene edge
                file if network smoothing is to be used, else None.
            gg_network_node_map_full_path (str): The path to the node map file
                if network smoothing is to be used, else None.
            gg_network_metadata_full_path (str): The path to the gene-gene edge
                metadata file if network smoothing is to be used, else None.
            network_influence (float): The amount of network influence to use.
            num_response_correlated_features (int): The number of top features
                from the correlation analysis to carry over to the network
                analysis.
            num_exported_features (int): The number of top features per
                phenotype for the pipeline to export in tsv.
            use_bootstrapping (bool): Whether to use bootstrapping.
            num_bootstraps (int): The number of bootstraps to run.
            bootstrap_sample_percent (float): The percentage of columns to use
                per bootstrap.
            prep_job (DataCleanupJob): The job that prepares the inputs.

        Returns:
            None: None.

        """
        job_name = 'nest-fp-' + correlation_method.replace('_', '').lower() + \
            '-' + job_id.to_slug().lower()
        LOGGER.debug(job_name + '.__init__')
        self.features_file_relative_path = features_file_relative_path
        self.gene_names_map_relative_path = gene_names_map_relative_path
        self.gene_names_mapped_and_unmapped_relative_path = \
            gene_names_mapped_and_unmapped_relative_path
        self.response_file_relative_path = response_file_relative_path
        self.gg_network_node_map_full_path = gg_network_node_map_full_path
        self.gg_network_metadata_full_path = gg_network_metadata_full_path
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
            'top_gamma_of_sort': num_exported_features
        }

        image = None
        if gg_network_name_full_path is not None:
            run_data['gg_network_name_full_path'] = gg_network_name_full_path
            run_data['rwr_max_iterations'] = 100
            run_data['rwr_convergence_tolerence'] = 1.0e-4
            run_data['rwr_restart_probability'] = \
                float(network_influence)/100
            run_data['top_beta_of_sort'] = num_response_correlated_features
            image = 'knowengdev/gene_prioritization_pipeline:01_25_2019'
        else:
            # pipeline has top_beta_of_sort parameter but doesn't use RWR;
            # setting to num_exported_features for now; not clear what pipeline
            # team might do with it later
            run_data['top_beta_of_sort'] = num_exported_features
            image = 'knowengdev/feature_prioritization_pipeline:09_27_2019'

        # note AWS m4.xl is 4 CPUS, 16 GB
        max_cpus = 4
        max_ram_mb = 14500
        run_data['max_cpu'] = max_cpus
        run_data['docker_image'] = image

        if use_bootstrapping:
            run_data['number_of_bootstraps'] = num_bootstraps
            run_data['rows_sampling_fraction'] = 1.0
            run_data['cols_sampling_fraction'] = \
                float(bootstrap_sample_percent)/100
        if gg_network_name_full_path is not None and use_bootstrapping:
            run_data['method'] = 'bootstrap_net_correlation'
        elif gg_network_name_full_path is not None and not use_bootstrapping:
            run_data['method'] = 'net_correlation'
        elif gg_network_name_full_path is None and use_bootstrapping:
            run_data['method'] = 'bootstrap_correlation'
        else:
            run_data['method'] = 'correlation'

        self.yml_path = os.path.join(self.job_dir_path, 'run.yml')
        with open(self.yml_path, 'wb') as outfile:
            yaml.safe_dump(run_data, outfile, default_flow_style=False)

        super(FeaturePrioritizationJob, self).__init__(\
            user_id, job_id, project_id, userfiles_dir, job_dir_relative_path, \
            job_name, timeout, cloud, image, max_cpus, max_ram_mb)

    def get_command(self):
        """Returns the docker command for feature prioritization."""
        LOGGER.debug(self.job_name + '.get_command')
        py_file = 'gene_prioritization' if self.gg_network_metadata_full_path \
            is not None else 'feature_prioritization'
        return 'date && cd ' + \
            os.path.join(PipelineJob.get_cloud_path(self.cloud), \
                'userfiles', self.job_dir_relative_path) + \
            ' && python3 /home/src/' + py_file + '.py ' + \
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
        return_val = False
        for name in os.listdir(self.results_dir_path):
            if name.startswith('top_genes_per_phenotype') or \
                    name.startswith('top_features_per_response'):
                return_val = True
        LOGGER.debug(self.job_name + '.is_done? ' + str(return_val))
        return return_val

    def on_done(self):
        """Processes scores, loads data to database, prepares zip file, and
        deletes self from the executor.

            Returns:
                None: None.

        """
        LOGGER.debug(self.job_name + '.on_done')
        scores = {}
        # 1. load the mapping from feature ids to feature names
        complete_feature_id_to_name = {}
        if self.gene_names_map_relative_path is not None:
            gnm_path = os.path.join(self.userfiles_dir,\
                self.gene_names_map_relative_path)
            complete_feature_id_to_name = get_dict_from_id_to_name(\
                gnm_path, self.gg_network_node_map_full_path)
        # 2. determine which features are ranked in the top 100 for
        # any response (or if there are fewer than 100 total features, get
        # however many we have)
        n_per_feature, feature_ids_set = self.get_top_feature_ids(100)
        # 3. for each response, load the scores for all features in
        # feature_ids_set. also find the minimum score found at rank
        # n_per_feature across all responses
        min_score_at_n = float('inf')
        feature_id_key = 'Gene_ENSEMBL_ID' if \
            self.gg_network_metadata_full_path is not None else 'Feature_ID'
        for name in self.get_response_files():
            csvfile_path = os.path.join(self.results_dir_path, name)
            with open(csvfile_path, 'rb') as csvfile:
                for row in csv.DictReader(csvfile, delimiter='\t'):
                    resp = row['Response']
                    if resp not in scores:
                        scores[resp] = {}
                    feature_id = row[feature_id_key]
                    if feature_id in feature_ids_set:
                        score = float(row['visualization_score'])
                        scores[resp][feature_id] = score
                        # the next check works because the file's rows are
                        # sorted by visualization score, and the first
                        # n_per_feature rows in the file correspond to features
                        # guaranteed to be in feature_ids_set
                        if len(scores[resp]) == n_per_feature:
                            min_score_at_n = min(min_score_at_n, score)
                        if len(scores[resp]) == len(feature_ids_set):
                            break
        # 4. drop any scores less than min_score_at_n
        for response, feature_dict in scores.iteritems():
            features_to_drop = []
            for feature, score in feature_dict.iteritems():
                if score < min_score_at_n:
                    features_to_drop.append(feature)
            for feature in features_to_drop:
                del feature_dict[feature]
        # 5. map feature ids and store results in db
        seen_feature_id_to_name = {feature_id: \
            complete_feature_id_to_name.get(feature_id, feature_id) \
            for feature_id in feature_ids_set}
        create_fp_record(self.user_id, self.job_id, scores, min_score_at_n,\
            seen_feature_id_to_name)
        # 6. create download zip and new spreadsheets
        output_file_info = self.prepare_output_files(\
            complete_feature_id_to_name)
        self.capture_files_in_db(output_file_info)
        self.capture_files_in_zip(output_file_info)
        # 7. clean up
        self.delete_job_record()

    def get_top_feature_ids(self, desired_top_n):
        """Finds the top N features for each response and returns a set
        constituting the union of those features. If it turns out the analysis
        has fewer than N features, will instead use however many features are
        actually available.

        Args:
            desired_top_n (int): The N the caller wishes to use. If the analysis
                has fewer than desired_top_n features, actual_top_n will be less
                than desired_top_n.

        Returns:
            int: The actual top N (actual_top_n) used. This will be equal to
                desired_top_n unless the analysis has fewer than desired_top_n
                features, in which case actual_top_n will be equal to the number
                of available features.
            set: A set containing the top feature ids.

        """
        # find the ranked features file
        rankfile_path = None
        for fname in os.listdir(self.results_dir_path):
            if fname.startswith('ranked_genes_per_phenotype') or \
                    fname.startswith('ranked_features_per_response'):
                rankfile_path = os.path.join(self.results_dir_path, fname)
        # process the ranked features file
        actual_top_n = 0
        return_set = set()
        with open(rankfile_path, 'r') as rankfile:
            for line in rankfile:
                pieces = line.rstrip().split("\t")
                # if line isn't header...
                if pieces[0] != '':
                    actual_top_n = int(pieces[0])
                    return_set.update(pieces[1:])
                    if actual_top_n == desired_top_n:
                        break
        return actual_top_n, return_set

    def get_response_files(self):
        """Returns a list of filenames for the response files.

            Returns:
                list: A list of the filenames for the response files.

        """
        return [f for f in os.listdir(self.results_dir_path) \
            if not f.startswith('ranked_genes_per_phenotype') and \
            not f.startswith('ranked_features_per_response') and \
            not f.startswith('top_genes_per_phenotype') and \
            not f.startswith('top_features_per_response') and \
            os.path.isfile(os.path.join(self.results_dir_path, f))]

    def prepare_output_files(self, feature_id_to_name):
        """Transforms output files in preparation for capture as new file
        records in the DB and/or as members of the download zip.

        Args:
            feature_id_to_name (dict): A dictionary from feature id to feature
                name.

         Returns:
            list: A list of dicts. Each dict represents a single output file and
                contains keys 'path', 'name', 'in_db', and 'in_zip'.

         """
        output_file_info = []

        cleaned_features_path = os.path.join(\
            self.userfiles_dir, self.features_file_relative_path)
        if self.gg_network_metadata_full_path is not None:
            transformed_features_file_path = \
                cleaned_features_path + ".transformed"
            map_first_column_of_file(\
                cleaned_features_path, \
                transformed_features_file_path, \
                feature_id_to_name)
            output_file_info.append({
                'path': transformed_features_file_path,
                'name': 'clean_features_matrix.txt',
                'in_db': False,
                'in_zip': True
            })
        else:
            output_file_info.append({
                'path': cleaned_features_path,
                'name': 'clean_features_matrix.txt',
                'in_db': False,
                'in_zip': True
            })

        cleaned_response_path = os.path.join(\
            self.userfiles_dir, self.response_file_relative_path)
        output_file_info.append({
            'path': cleaned_response_path,
            'name': 'clean_phenotypic_matrix.txt',
            'in_db': False,
            'in_zip': True
        })

        # combine viz files
        combined_viz_path = os.path.join(self.job_dir_path, 'combined_viz.tsv')
        with open(combined_viz_path, 'w') as combo:
            for fidx, fname in enumerate(sorted(self.get_response_files())):
                fpath = os.path.join(self.results_dir_path, fname)
                with open(fpath, 'r') as vizfile:
                    for lidx, line in enumerate(vizfile):
                        if lidx == 0:
                            # only print the column labels once
                            if fidx == 0:
                                cleaned = line.replace(\
                                    'Gene_ENSEMBL_ID', 'Feature_ID')
                                combo.write(cleaned)
                        else:
                            pieces = line.rstrip().split("\t")
                            combo.write(pieces[0] + "\t" + \
                                "\t".join([\
                                    feature_id_to_name.get(piece, piece) for \
                                    piece in pieces[1:]]) + \
                                "\n")
        output_file_info.append({
            'path': combined_viz_path,
            'name': 'features_ranked_per_phenotype.txt',
            'in_db': True,
            'in_zip': True
        })

        top_features_files = [f for f in os.listdir(self.results_dir_path) \
            if f.startswith('top_genes_per_phenotype') or \
            f.startswith('top_features_per_response')]
        if len(top_features_files) == 1:
            top_features_file_path = os.path.join(\
                self.results_dir_path, top_features_files[0])
            transformed_top_features_file_path = top_features_file_path + \
                ".transformed"
            map_first_column_of_file(\
                top_features_file_path, \
                transformed_top_features_file_path, \
                feature_id_to_name)
            output_file_info.append({
                'path': transformed_top_features_file_path,
                'name': 'top_features_per_phenotype_matrix.txt',
                'in_db': True,
                'in_zip': True
            })

        output_file_info.append({
            'path': '/pipeline_readmes/README-FP.md',
            'name': 'README-FP.md',
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

        if self.gene_names_mapped_and_unmapped_relative_path is not None:
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

def get_feature_prioritization_runners(\
    user_id, job_id, project_id, userfiles_dir, project_dir, timeout, cloud,\
    species_id, features_file_id, response_file_id, correlation_method,\
    missing_values_method, use_network, network_name, network_influence,\
    num_response_correlated_features, num_exported_features, use_bootstrapping,\
    num_bootstraps, bootstrap_sample_percent):
    """Returns a list of PipelineJob instances required to run an FP job.

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
        species_id (str): The species_id to disambiguate networks with
            identical edge_type_names.
        features_file_id (NestId): The _id of the features file in the database.
        response_file_id (NestId): The _id of the response file in the database.
        correlation_method (str): One of ['pearson', 't_test', 'edgeR'].
        missing_values_method (str): One of ['average', 'remove', 'reject'].
        use_network (bool): Whether to use the knowledge network.
        network_name (str): The network to use when use_network is True.
        network_influence (float): The amount of network influence to use.
        num_response_correlated_features (int): The number of top features from
            the correlation analysis to carry over to the network analysis.
        num_exported_features (int): The number of top features per phenotype
            for the pipeline to export in tsv.
        use_bootstrapping (bool): Whether to use bootstrapping.
        num_bootstraps (int): The number of bootstraps to run.
        bootstrap_sample_percent (float): The percentage of columns to use
            per bootstrap.

    Returns:
        list: A list of PipelineJob instances required to run an FP job.

    """
    job_name = "nest-fp-" + correlation_method.lower() + '-' + \
        job_id.to_slug().lower()
    job_dir_relative_path = os.path.join(project_dir, job_name)
    os.mkdir(os.path.join(userfiles_dir, job_dir_relative_path))

    features_file_dto = get_file_record(user_id, features_file_id)
    cleaned_features_file_relative_path = \
        get_cleaned_spreadsheet_relative_path(\
            job_dir_relative_path, features_file_dto)

    gene_names_map_relative_path = None
    gene_names_mapped_and_unmapped_relative_path = None
    if use_network:
        gene_names_map_relative_path = \
            get_gene_names_map_relative_path(\
                job_dir_relative_path, features_file_dto)
        gene_names_mapped_and_unmapped_relative_path = \
            get_gene_names_mapped_and_unmapped_relative_path(\
                job_dir_relative_path, features_file_dto)

    response_file_dto = get_file_record(user_id, response_file_id)
    response_file_relative_path = \
        get_cleaned_spreadsheet_relative_path(\
            job_dir_relative_path, response_file_dto)

    gg_network_name_full_path = None
    gg_network_node_map_full_path = None
    gg_network_metadata_full_path = None
    if use_network:
        networks = get_merged_network_info('/networks/')
        match = [net for net in networks if \
            net['species_id'] == species_id and \
            net['edge_type_name'] == network_name][0]
        gg_network_name_full_path = '../../../networks/' + match['path_to_edge']
        gg_network_node_map_full_path = '../../../networks/' + \
            match['path_to_node_map']
        gg_network_metadata_full_path = '../../../networks/' + \
            match['path_to_metadata']

    dc_method = None
    if correlation_method == 't_test':
        dc_method = CorrelationMeasure.T_TEST
    elif correlation_method == 'pearson':
        dc_method = CorrelationMeasure.PEARSON
    elif correlation_method == 'edgeR':
        dc_method = CorrelationMeasure.EDGER
    else:
        # TODO error
        pass
    na_method = None
    if missing_values_method == 'average':
        na_method = MissingValuesMethod.AVERAGE
    elif missing_values_method == 'remove':
        na_method = MissingValuesMethod.REMOVE
    elif missing_values_method == 'reject':
        na_method = MissingValuesMethod.REJECT
    else:
        # TODO error
        pass
    prep_job = DataCleanupJob(\
        user_id, job_id, project_id, userfiles_dir, timeout, cloud, species_id,
        features_file_dto, response_file_dto, gg_network_name_full_path,
        job_dir_relative_path, PipelineType.FEATURE_PRIORITIZATION, dc_method,
        na_method)
    return [
        prep_job,
        FeaturePrioritizationJob(\
            user_id, job_id, project_id, userfiles_dir, job_dir_relative_path,
            timeout, cloud, cleaned_features_file_relative_path,
            gene_names_map_relative_path,
            gene_names_mapped_and_unmapped_relative_path,
            response_file_relative_path, correlation_method,
            gg_network_name_full_path, gg_network_node_map_full_path,
            gg_network_metadata_full_path, network_influence,
            num_response_correlated_features, num_exported_features,
            use_bootstrapping, num_bootstraps, bootstrap_sample_percent,
            prep_job)
    ]
