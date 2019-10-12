"""This module defines a class for running knoweng's sample clustering jobs."""

import logging
import os
import re
from zipfile import ZipFile, ZIP_DEFLATED

import pandas as pd
import yaml

from nest_py.knoweng.jobs.db_utils import create_sc_record, get_file_record, \
    create_file_record
from nest_py.knoweng.jobs.networks import get_merged_network_info
from nest_py.knoweng.jobs.pipeline_job import PipelineJob
from nest_py.knoweng.jobs.pipelines.data_cleanup import \
    DataCleanupJob, PipelineType, get_dict_from_id_to_name, \
    get_cleaned_spreadsheet_relative_path, get_gene_names_map_relative_path, \
    get_gene_names_mapped_and_unmapped_relative_path, map_first_column_of_file
from nest_py.knoweng.jobs.pipelines.spreadsheet_visualization import \
    SpreadsheetVisualizationJob

LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.INFO)

class SampleClusteringComputeJob(PipelineJob):
    """Subclass of PipelineJob that handles sample clustering jobs."""
    def __init__(self, user_id, job_id, project_id, userfiles_dir,
                 job_dir_relative_path, job_name, timeout, cloud,
                 features_file_relative_path, gene_names_map_relative_path,
                 gene_names_mapped_and_unmapped_relative_path,
                 response_file_relative_path, num_clusters, method,
                 affinity_metric, linkage_criterion, num_nearest_neighbors,
                 gg_network_name_full_path, gg_network_node_map_full_path,
                 gg_network_metadata_full_path, network_smoothing,
                 use_bootstrapping, num_bootstraps, bootstrap_sample_percent,
                 prep_job, postprocessing_job):
        """Initializes self.

        Args:
            user_id (NestId): The user id associated with the job.
            job_id (NestId): The job id associated with the job.
            project_id (NestId): The project id associated with the job.
            userfiles_dir (str): The base directory containing all files for
                all users.
            job_dir_relative_path (str): The relative path from userfiles_dir
                to the directory containing the job's files, which must already
                exist.
            job_name (str): The job name.
            timeout (int): The maximum execution time in seconds.
            cloud (str): The cloud name, which must appear as a key in
                your executor's cloud_path_dict.
            features_file_relative_path (str): The relative path from the
                userfiles_dir to the features file.
            gene_names_map_relative_path (str): The relative path from the
                userfiles_dir to the gene-name map, or None if no gene-name
                mapping will be done.
            gene_names_mapped_and_unmapped_relative_path (str): The relative
                path from the userfiles_dir to the file of all gene names,
                mapped and unmapped, or None if no gene-name mapping will be
                done.
            response_file_relative_path (str): The relative path from the
                userfiles_dir to the response file.
            num_clusters (int): The number of clusters to form.
            method (str): One of ['K-means', 'Hierarchical',
                'Linked Hierarchical'].
            affinity_metric (str): One of ['euclidean', 'manhattan', 'jaccard']
                or None if the method is K-means.
            linkage_criterion (str): One of ['average', 'complete', 'ward'] or
                None if the method is K-means.
            num_nearest_neighbors (int): The number of neighbor clusters to
                consider if Linked Hierarchical clustering.
            gg_network_name_full_path (str): The path to the gene-gene edge
                file if network smoothing is to be used, else None.
            gg_network_node_map_full_path (str): The path to the node map file
                if network smoothing is to be used, else None.
            gg_network_metadata_full_path (str): The path to the gene-gene edge
                metadata file if network smoothing is to be used, else None.
            network_smoothing (float): The amount of network smoothing to use.
            use_bootstrapping (bool): Whether to use bootstrapping.
            num_bootstraps (int): The number of bootstraps to run.
            bootstrap_sample_percent (float): The percentage of columns to use
                per bootstrap.
            prep_job (DataCleanupJob): The job that prepares the inputs.
            postprocessing_job (SampleClusteringPostprocessingJob): The job that
                processes the outputs for the visualization.

        Returns:
            None: None.

        """
        LOGGER.debug(job_name + '.__init__')
        self.features_file_relative_path = features_file_relative_path
        self.gene_names_map_relative_path = gene_names_map_relative_path
        self.gene_names_mapped_and_unmapped_relative_path = \
            gene_names_mapped_and_unmapped_relative_path
        self.response_file_relative_path = response_file_relative_path
        self.gg_network_node_map_full_path = gg_network_node_map_full_path
        self.gg_network_metadata_full_path = gg_network_metadata_full_path
        self.prep_job = prep_job
        self.postprocessing_job = postprocessing_job
        self.use_bootstrapping = use_bootstrapping

        # these will be populated by prepare_output_files
        self.cluster_labels_file_info_item = None
        self.silhouette_scores_per_sample_file_info_item = None
        self.consensus_matrix_file_info_item = None

        self.job_dir_path = os.path.join(userfiles_dir, job_dir_relative_path)

        self.results_dir_path = os.path.join(self.job_dir_path, 'results')
        os.mkdir(self.results_dir_path)

        max_num_threads = 4 # AWS m4.xl is 4 CPUS, 16 GB

        # create yaml file
        run_data = {
            'spreadsheet_name_full_path': '../../' + features_file_relative_path,
            'results_directory': './results',
            'processing_method': 'parallel',
            'parallelism': max_num_threads,
            'number_of_clusters': num_clusters,
            'tmp_directory': './tmp'
        }
        if response_file_relative_path is not None:
            run_data['phenotype_name_full_path'] = \
                '../../' + response_file_relative_path
            run_data['threshold'] = 15

        run_data['nmf_conv_check_freq'] = 50
        run_data['nmf_max_invariance'] = 200
        run_data['nmf_max_iterations'] = 10000
        run_data['nmf_penalty_parameter'] = 1400

        image = None
        if gg_network_name_full_path is not None:
            run_data['gg_network_name_full_path'] = gg_network_name_full_path
            run_data['rwr_max_iterations'] = 100
            run_data['rwr_convergence_tolerence'] = 1.0e-4
            run_data['rwr_restart_probability'] = \
                float(network_smoothing)/100
            run_data['top_number_of_genes'] = 100
            image = 'knowengdev/samples_clustering_pipeline:08_23_2018'
        else:
            run_data['top_number_of_rows'] = 100
            run_data['affinity_metric'] = affinity_metric
            run_data['linkage_criterion'] = linkage_criterion
            image = 'knowengdev/general_clustering_pipeline:08_23_2018'

        run_data['docker_image'] = image

        if use_bootstrapping:
            run_data['number_of_bootstraps'] = num_bootstraps
            run_data['rows_sampling_fraction'] = 1.0
            run_data['cols_sampling_fraction'] = \
                float(bootstrap_sample_percent)/100
        if gg_network_name_full_path is not None and use_bootstrapping:
            run_data['method'] = 'cc_net_nmf'
        elif gg_network_name_full_path is not None and not use_bootstrapping:
            run_data['method'] = 'net_nmf'
        elif gg_network_name_full_path is None and use_bootstrapping:
            if method == 'K-means':
                run_data['method'] = 'cc_kmeans'
            elif method == 'Hierarchical':
                run_data['method'] = 'cc_hclust'
            elif method == 'Linked Hierarchical':
                run_data['method'] = 'cc_link_hclust'
                run_data['nearest_neighbors'] = num_nearest_neighbors
            else:
                raise Exception(\
                    'Unknown method for no KN with bootstrapping:' + method)
        else:
            if method == 'K-means':
                run_data['method'] = 'kmeans'
            elif method == 'Hierarchical':
                run_data['method'] = 'hclust'
            elif method == 'Linked Hierarchical':
                run_data['method'] = 'link_hclust'
                run_data['nearest_neighbors'] = num_nearest_neighbors
            else:
                raise Exception(\
                    'Unknown method for no KN without bootstrapping:' + method)

        self.yml_path = os.path.join(self.job_dir_path, 'run.yml')
        with open(self.yml_path, 'wb') as outfile:
            yaml.safe_dump(run_data, outfile, default_flow_style=False)

        super(SampleClusteringComputeJob, self).__init__(\
            user_id, job_id, project_id, userfiles_dir, job_dir_relative_path,\
            job_name, timeout, cloud, image, max_num_threads, 14500)

    def get_command(self):
        """Returns the docker command for sample_clustering."""
        LOGGER.debug(self.job_name + '.get_command')
        py_file = 'samples_clustering' if self.gg_network_metadata_full_path \
            is not None else 'general_clustering'
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
        found_target1 = False
        found_target2 = False
        target1a_filename_fragment = 'top_genes_by_cluster_'
        target1b_filename_fragment = 'top_rows_by_cluster_'
        target2_filename_fragment = 'clustering_evaluation_result_'
        for name in os.listdir(self.results_dir_path):
            if name.startswith(target1a_filename_fragment) or \
                    name.startswith(target1b_filename_fragment):
                found_target1 = True
            if name.startswith(target2_filename_fragment):
                found_target2 = True
        return_val = found_target1
        if self.response_file_relative_path is not None:
            return_val = return_val and found_target2
        LOGGER.debug(self.job_name + '.is_done? ' + str(return_val))
        return return_val

    def on_done(self):
        """Processes scores, loads data to database, prepares zip file, and
        deletes self from the executor.

            Returns:
                None: None.

        """
        LOGGER.debug(self.job_name + '.on_done')
        # the exact filenames change with every run, so we'll have to find these
        features_average_per_cluster_file_path = None
        samples_label_by_cluster_file_path = None
        consensus_matrix_file_path = None
        top_features_by_cluster_file_path = None
        clustering_evaluation_file_path = None
        silhouette_scores_per_sample_file_path = None
        silhouette_scores_per_cluster_file_path = None
        silhouette_score_overall_file_path = None

        for name in os.listdir(self.results_dir_path):
            file_path = os.path.join(self.results_dir_path, name)
            if name.startswith('genes_averages_by_cluster_') or \
                    name.startswith('rows_averages_by_cluster_'):
                features_average_per_cluster_file_path = file_path
            elif name.startswith('samples_label_by_cluster_'):
                samples_label_by_cluster_file_path = file_path
            elif name.startswith('consensus_matrix_'):
                consensus_matrix_file_path = file_path
            elif name.startswith('top_genes_by_cluster_') or \
                    name.startswith('top_rows_by_cluster_'):
                top_features_by_cluster_file_path = file_path
            elif name.startswith('clustering_evaluation_result_'):
                clustering_evaluation_file_path = file_path
            elif name.startswith('silhouette_per_sample_score_'):
                silhouette_scores_per_sample_file_path = file_path
            elif name.startswith('silhouette_per_cluster_score_'):
                silhouette_scores_per_cluster_file_path = file_path
            elif name.startswith('silhouette_overall_score_'):
                silhouette_score_overall_file_path = file_path

        # prepare to map feature ids to feature names (important for case of
        # genes as features)
        # note that below we use `feature_id_to_name.get` with a default value,
        # which covers us in the case of non-gene feature names
        feature_id_to_name = {}
        if self.gene_names_map_relative_path is not None:
            gnm_path = os.path.join(self.userfiles_dir,\
                self.gene_names_map_relative_path)
            feature_id_to_name = get_dict_from_id_to_name(gnm_path, \
                self.gg_network_node_map_full_path)

        cluster_labels = self.get_cluster_labels(\
            samples_label_by_cluster_file_path)

        consensus_matrix_df = None
        if self.use_bootstrapping:
            consensus_matrix_df = self.get_consensus_df(\
                consensus_matrix_file_path)

        global_silhouette_score = self.get_overall_silhouette_score(\
            silhouette_score_overall_file_path)
        cluster_silhouette_scores = self.get_cluster_silhouette_scores(\
            cluster_labels, silhouette_scores_per_cluster_file_path)

        output_file_info = self.prepare_output_files(\
            top_features_by_cluster_file_path, consensus_matrix_file_path, \
            samples_label_by_cluster_file_path, cluster_labels, \
            clustering_evaluation_file_path, \
            silhouette_scores_per_sample_file_path, \
            silhouette_scores_per_cluster_file_path, \
            silhouette_score_overall_file_path, \
            features_average_per_cluster_file_path, feature_id_to_name)
        self.capture_files_in_db(output_file_info)
        self.capture_files_in_zip(output_file_info)

        consensus_matrix_file_id = \
            self.consensus_matrix_file_info_item['file_dto'].get_nest_id() \
            if self.use_bootstrapping else None
        cluster_labels_file_id = \
            self.cluster_labels_file_info_item['file_dto'].get_nest_id()
        initial_column_grouping_feature_index = 0
        silhouette_scores_per_sample_file_id = \
            self.silhouette_scores_per_sample_file_info_item[\
                'file_dto'].get_nest_id()
        initial_column_sorting_feature_index = 0
        create_sc_record(self.user_id, self.job_id, consensus_matrix_df,\
            consensus_matrix_file_id, cluster_labels_file_id,\
            initial_column_grouping_feature_index, \
            silhouette_scores_per_sample_file_id,\
            initial_column_sorting_feature_index, global_silhouette_score,\
            cluster_silhouette_scores)

        postprocessing_nest_ids = [\
            cluster_labels_file_id, silhouette_scores_per_sample_file_id]
        self.postprocessing_job.complete_configuration_and_mark_ready(\
            postprocessing_nest_ids)
        self.delete_job_record()

    def get_cluster_labels(self, samples_label_by_cluster_file_path):
        """Returns a series containing the cluster labels.

        Args:
            samples_label_by_cluster_file_path (str): The path to the file
                containing the cluster labels.

        Returns:
            pandas.Series: A series containing the cluster labels.

        """
        labels_df = pd.read_csv(samples_label_by_cluster_file_path,\
            delimiter='\t', index_col=0, header=None,\
            names=['cluster_assignment'])
        labels_df.index = labels_df.index.map(unicode)
        return labels_df.iloc[:, 0] # read_csv creates a df, but we return an s

    def get_consensus_df(self, consensus_matrix_file_path):
        """Returns a dataframe containing the consensus matrix.

        Args:
            consensus_matrix_file_path (str): The path to the file containing
                consensus clustering scores.

        Returns:
            pandas.DataFrame: A dataframe containing the consensus matrix.

        """
        df_consensus = pd.read_csv(\
            consensus_matrix_file_path, delimiter='\t', index_col=0)
        df_consensus.index = df_consensus.index.map(unicode)
        if df_consensus.index.tolist() != df_consensus.columns.tolist():
            raise Exception('Labels mismatch on consensus matrix.')
        return df_consensus

    def get_overall_silhouette_score(self, silhouette_score_overall_file_path):
        """Returns the overall silhouette score.

        Args:
            silhouette_score_overall_file_path (str): The path to the file
                containing the overall silhouette score.

        Returns:
            float: The overall silhouette score.

        """
        return_val = None
        with open(silhouette_score_overall_file_path, 'r') as infile:
            lines = infile.readlines()
        if len(lines) == 1:
            pieces = lines[0].rstrip().split("\t")
            if len(pieces) == 2:
                return_val = pieces[1]
            else:
                raise Exception('File of overall silhouette score had ' + \
                    str(len(pieces)) + ' columns.')
        else:
            raise Exception('File of overall silhouette score had ' + \
                str(len(lines)) +  ' lines.')
        return return_val

    def get_cluster_silhouette_scores(self, \
        cluster_labels, silhouette_scores_per_cluster_file_path):
        """Returns the cluster-level silhouette scores.

        Args:
            cluster_labels (list): The cluster labels. The list returned by
                this method will be ordered to match.
            silhouette_scores_per_cluster_file_path (str): The path to the file
                containing the cluster-level silhouette scores.

        Returns:
            list: The cluster-level silhouette scores, ordered to match
                `cluster_labels`.

        """
        cluster_label_to_score = {}
        with open(silhouette_scores_per_cluster_file_path, 'r') as infile:
            for line in infile:
                pieces = line.rstrip().split("\t")
                if len(pieces) == 2:
                    cluster_label_to_score[pieces[0]] = pieces[1]
                else:
                    raise Exception(\
                        'File of cluster-level silhouette scores had ' + \
                        str(len(pieces)) + ' columns.')
        return [cluster_label_to_score[str(label)] for label in cluster_labels]

    def add_headers_to_file(self, file_path, headers_array):
        """Adds headers to a file that currently has no headers. Will read the
        current file contents into memory, so only use on smaller files.

        Args:
            file_path (str): The path to the file. The original file will be
                overwritten with the new file.
            headers_array (list): A list of strings that should be used as
                headers in the file.

        Returns:
            None.

        """
        with open(file_path, 'r') as infile:
            lines = infile.readlines()
        with open(file_path, 'w') as outfile:
            outfile.write("\t".join(headers_array) + "\n")
            for line in lines:
                outfile.write(line)

    def prepare_output_files(self, top_features_by_cluster_file_path, \
        consensus_matrix_file_path, samples_label_by_cluster_file_path, \
        cluster_labels, clustering_evaluation_file_path, \
        silhouette_scores_per_sample_file_path, \
        silhouette_scores_per_cluster_file_path, \
        silhouette_score_overall_file_path, \
        features_average_per_cluster_file_path, feature_id_to_name):
        """Transforms output files in preparation for capture as new file
        records in the DB and/or as members of the download zip.

        Args:
            top_features_by_cluster_file_path (str): The path to the file
                containing top features per cluster.
            consensus_matrix_file_path (str): The path to the file
                containing consensus clustering scores.
            samples_label_by_cluster_file_path (str): The path to the file
                containing sample labels with their cluster labels.
            cluster_labels (pandas.Series): The cluster labels for each sample.
            clustering_evaluation_file_path (str): The path to the file
                containing clustering evaluation data.
            silhouette_scores_per_sample_file_path (str): The path to the file
                containing sample-level silhouette scores.
            silhouette_scores_per_cluster_file_path (str): The path to the file
                containing cluster-level silhouette scores.
            silhouette_score_overall_file_path (str): The path to the file
                containing the overall silhouette score.
            features_average_per_cluster_file_path (str): The path to the file
                containing feature averages per cluster.
            feature_id_to_name (dict): A dictionary from feature id to feature
                name.

        Returns:
           list: A list of dicts. Each dict represents a single output file and
               contains keys 'path', 'name', 'in_db', and 'in_zip'.

        """
        output_file_info = []

        # write out cluster labels (need new copy b/c original doesn't include
        # header)
        transformed_samples_label_by_cluster_file_path = \
            samples_label_by_cluster_file_path + ".transformed"
        cluster_labels.to_csv(transformed_samples_label_by_cluster_file_path, \
            sep="\t", header=True)

        self.cluster_labels_file_info_item = {
            'path': transformed_samples_label_by_cluster_file_path,
            'name': 'sample_labels_by_cluster.txt',
            'in_db': True,
            'in_zip': True
        }
        output_file_info.append(self.cluster_labels_file_info_item)

        cleaned_features_path = os.path.join(self.userfiles_dir, \
            self.features_file_relative_path)
        if self.gg_network_metadata_full_path is not None:

            # undo mappings
            transformed_features_file_path = \
                cleaned_features_path + ".transformed"
            map_first_column_of_file(\
                cleaned_features_path, \
                transformed_features_file_path, \
                feature_id_to_name)

            transformed_features_average_per_cluster_file_path = \
                features_average_per_cluster_file_path + ".transformed"
            map_first_column_of_file(\
                features_average_per_cluster_file_path, \
                transformed_features_average_per_cluster_file_path, \
                feature_id_to_name)

            transformed_top_features_by_cluster_file_path = \
                top_features_by_cluster_file_path + ".transformed"
            map_first_column_of_file(\
                top_features_by_cluster_file_path, \
                transformed_top_features_by_cluster_file_path, \
                feature_id_to_name)

        else:
            # no mappings to undo
            transformed_features_file_path = cleaned_features_path
            transformed_features_average_per_cluster_file_path = \
                features_average_per_cluster_file_path
            transformed_top_features_by_cluster_file_path = \
                top_features_by_cluster_file_path

        output_file_info.append({
            'path': transformed_features_file_path,
            'name': 'clean_features_matrix.txt',
            'in_db': False,
            'in_zip': True
        })
        output_file_info.append({
            'path': transformed_features_average_per_cluster_file_path,
            'name': 'feature_avgs_by_cluster.txt',
            'in_db': True,
            'in_zip': True
        })
        output_file_info.append({
            'path': transformed_top_features_by_cluster_file_path,
            'name': 'top_features_by_cluster.txt',
            'in_db': True,
            'in_zip': True
        })
        if consensus_matrix_file_path is not None:
            self.consensus_matrix_file_info_item = {
                'path': consensus_matrix_file_path,
                'name': 'consensus_matrix.txt',
                'in_db': True,
                'in_zip': True
            }
            output_file_info.append(self.consensus_matrix_file_info_item)
        if clustering_evaluation_file_path is not None:
            output_file_info.append({
                'path': clustering_evaluation_file_path,
                'name': 'clustering_evaluations.txt',
                'in_db': True,
                'in_zip': True
            })
        # add headers to silhouette-score files
        self.add_headers_to_file(silhouette_scores_per_sample_file_path, \
            ['', 'silhouette_score'])
        self.silhouette_scores_per_sample_file_info_item = {
            'path': silhouette_scores_per_sample_file_path,
            'name': 'silhouette_scores_per_sample.txt',
            'in_db': True,
            'in_zip': True
        }
        output_file_info.append(\
            self.silhouette_scores_per_sample_file_info_item)

        self.add_headers_to_file(silhouette_scores_per_cluster_file_path, \
            ['', 'silhouette_score'])
        output_file_info.append({
            'path': silhouette_scores_per_cluster_file_path,
            'name': 'silhouette_scores_per_cluster.txt',
            'in_db': False,
            'in_zip': True
        })

        self.add_headers_to_file(silhouette_score_overall_file_path, \
            ['', 'silhouette_score'])
        output_file_info.append({
            'path': silhouette_score_overall_file_path,
            'name': 'silhouette_score_overall.txt',
            'in_db': False,
            'in_zip': True
        })

        output_file_info.append({
            'path': '/pipeline_readmes/README-SC.md',
            'name': 'README-SC.md',
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
                item['file_dto'] = create_file_record(\
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

class SampleClusteringPostprocessingJob(SpreadsheetVisualizationJob):

    """Local job that prepares the visualization."""
    def __init__(self, user_id, job_id, project_id, userfiles_dir,\
        job_dir_relative_path, job_name, features_file_id, response_file_id):
        """Initializes self.

        Args:
            user_id (NestId): The user id associated with the job.
            job_id (NestId): The job id associated with the job.
            project_id (NestId): The project id associated with the job.
            userfiles_dir (str): The base directory containing all files for
                all users.
            job_dir_relative_path (str): The relative path from userfiles_dir
                to the directory containing the job's files, which must already
                exist.
            job_name (str): The job name.
            features_file_id (NestID): The NestId of the features file in the
                database.
            response_file_id (NestID): The NestId of the response file in the
                database, or None if no response file was selected.

        Returns:
            None: None.

        """
        self.is_configured = False
        spreadsheet_ids = [features_file_id]
        if response_file_id is not None:
            spreadsheet_ids.append(response_file_id)

        super(SampleClusteringPostprocessingJob, self).__init__(\
            user_id, job_id, project_id, userfiles_dir, job_dir_relative_path,\
            job_name, spreadsheet_ids)

    def complete_configuration_and_mark_ready(self, new_spreadsheet_nest_ids):
        """Adds file information generated during execution of the compute job
        to the scope of work for this instance.

        Args:
            new_spreadsheet_nest_ids: The data files genereated by the compute
                job.

        Returns:
            None: None.

        """
        self.spreadsheet_nest_ids.extend(new_spreadsheet_nest_ids)
        self.is_configured = True

    def start(self):
        """Processes all spreadsheet data to populate database tables. Overrides
        parent class implementation to remove call to prepare_zip_file().

        Returns:
            None: None.

        """
        self.process_data()
        self.started = True

    def is_ready(self):
        """Overrides parent class implementation so that execution won't start
        until the compute job has finished."""
        return self.is_configured

def get_sample_clustering_runners(\
    user_id, job_id, project_id, userfiles_dir, project_dir, timeout, cloud,\
    species_id, features_file_id, response_file_id, num_clusters, method,\
    affinity_metric, linkage_criterion, num_nearest_neighbors, use_network,\
    network_name, network_smoothing, use_bootstrapping, num_bootstraps,\
    bootstrap_sample_percent):
    """Returns a list of PipelineJob instances required to run an SC job.

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
        features_file_id (NestId): The NestId of the features file in the
            database.
        response_file_id (NestID): The NestId of the response file in the
            database, or None if no response file was selected.
        num_clusters (int): The number of clusters to form.
        method (str): One of ['K-means', 'Hierarchical', 'Linked Hierarchical'].
        affinity_metric (str): One of ['euclidean', 'manhattan', 'jaccard'] or
            None if the method is K-means.
        linkage_criterion (str): One of ['average', 'complete', 'ward'] or
            None if the method is K-means.
        num_nearest_neighbors (int): The number of neighbor clusters to
            consider if Linked Hierarchical clustering.
        use_network (bool): Whether to use the knowledge network.
        network_name (str): The network to use when use_network is True.
        network_smoothing (float): The amount of network smoothing to use.
        use_bootstrapping (bool): Whether to use bootstrapping.
        num_bootstraps (int): The number of bootstraps to run.
        bootstrap_sample_percent (float): The percentage of columns to use
            per bootstrap.

    Returns:
        list: A list of PipelineJob instances required to run an SC job.

    """
    job_name = "nest-sc-" + re.sub(r'[^A-Za-z0-9]', '', method).lower() + \
        '-' + job_id.to_slug().lower()
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

    response_file_dto = None
    response_file_relative_path = None
    if response_file_id is not None:
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

    prep_job = DataCleanupJob(\
        user_id, job_id, project_id, userfiles_dir, timeout, cloud, species_id,\
        features_file_dto, response_file_dto, gg_network_name_full_path,\
        job_dir_relative_path, PipelineType.SAMPLE_CLUSTERING, None, None)
    postprocessing_job = SampleClusteringPostprocessingJob(\
        user_id, job_id, project_id, userfiles_dir, job_dir_relative_path,\
        job_name + '-postprocessing', features_file_id, response_file_id)
    compute_job = SampleClusteringComputeJob(\
        user_id, job_id, project_id, userfiles_dir, job_dir_relative_path,\
        job_name, timeout, cloud, cleaned_features_file_relative_path,\
        gene_names_map_relative_path,\
        gene_names_mapped_and_unmapped_relative_path,\
        response_file_relative_path, num_clusters, method, affinity_metric,\
        linkage_criterion, num_nearest_neighbors,\
        gg_network_name_full_path, gg_network_node_map_full_path,\
        gg_network_metadata_full_path, network_smoothing,\
        use_bootstrapping, num_bootstraps, bootstrap_sample_percent,\
        prep_job, postprocessing_job)
    return [prep_job, compute_job, postprocessing_job]
