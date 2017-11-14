"""This module defines a class for running knoweng's sample clustering jobs."""

from math import isnan
import os
from zipfile import ZipFile, ZIP_DEFLATED

import pandas as pd
import yaml

from nest_py.knoweng.jobs.chronos_job import ChronosJob
from nest_py.knoweng.jobs.db_utils import create_sc_record, get_file_record
from nest_py.knoweng.jobs.networks import get_merged_network_info
from nest_py.knoweng.jobs.data_cleanup import \
    DataCleanupJob, PipelineType, get_dict_from_id_to_name, \
    get_cleaned_spreadsheet_relative_path, get_gene_names_map_relative_path

class SampleClusteringJob(ChronosJob):
    """Subclass of ChronosJob that handles sample clustering jobs."""
    def __init__(self, user_id, job_id, userfiles_dir, job_dir_relative_path,
                 timeout, cloud, features_file_relative_path,
                 gene_names_map_relative_path, response_file_relative_path,
                 method, num_clusters, gg_network_name_full_path,
                 gg_network_metadata_full_path, network_smoothing,
                 use_bootstrapping, num_bootstraps, bootstrap_sample_percent,
                 prep_job):
        """Initializes self.

        Args:
            user_id (NestId): The user id associated with the job.
            job_id (NestId): The unique identifier Eve/Mongo assigns to the job.
            userfiles_dir (str): The base directory containing all files for
                all users.
            job_dir_relative_path (str): The relative path from userfiles_dir
                to the directory containing the job's files, which must already
                exist.
            timeout (int): The maximum execution time in seconds.
            cloud (str): The cloud name, which must appear as a key in
                nest_py.knoweng.jobs.ChronosJob.cloud_path_dict.
            features_file_relative_path (str): The relative path from the
                userfiles_dir to the features file.
            gene_names_map_relative_path (str): The relative path from the
                userfiles_dir to the gene-name map.
            response_file_relative_path (str): The relative path from the
                userfiles_dir to the response file.
            method (str): One of ['K-means'].
            num_clusters (int): The number of clusters to form.
            gg_network_name_full_path (str): The path to the gene-gene edge
                file if network smoothing is to be used, else None.
            gg_network_metadata_full_path (str): The path to the gene-gene edge
                metadata file if network smoothing is to be used, else None.
            network_smoothing (float): The amount of network smoothing to use.
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
        self.gg_network_metadata_full_path = gg_network_metadata_full_path
        self.prep_job = prep_job

        self.job_dir_path = os.path.join(userfiles_dir, job_dir_relative_path)

        self.results_dir_path = os.path.join(self.job_dir_path, 'results')
        os.mkdir(self.results_dir_path)

        max_num_threads = 8

        # create yaml file
        run_data = {
            'spreadsheet_name_full_path': '../../' + features_file_relative_path,
            'results_directory': './results',
            'processing_method': 'parallel',
            'parallelism': max_num_threads,
            'number_of_clusters': num_clusters,
            'top_number_of_genes': 100,
            'tmp_directory': './tmp'
        }
        if response_file_relative_path is not None:
            run_data['phenotype_name_full_path'] = \
                '../../' + response_file_relative_path
            run_data['threshold'] = 10

        # TODO may need to distinguish between initial clustering method
        # and final clustering method
        # for now, the user doesn't have any real control
        run_data['nmf_conv_check_freq'] = 50
        run_data['nmf_max_invariance'] = 200
        run_data['nmf_max_iterations'] = 10000
        run_data['nmf_penalty_parameter'] = 1400

        if gg_network_name_full_path is not None:
            run_data['gg_network_name_full_path'] = gg_network_name_full_path
            run_data['rwr_max_iterations'] = 100
            run_data['rwr_convergence_tolerence'] = 1.0e-4
            run_data['rwr_restart_probability'] = \
                1 - float(network_smoothing)/100
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
            run_data['method'] = 'cc_nmf'
        else:
            run_data['method'] = 'nmf'

        self.yml_path = os.path.join(self.job_dir_path, 'run.yml')
        with open(self.yml_path, 'wb') as outfile:
            yaml.safe_dump(run_data, outfile, default_flow_style=False)

        basename = 'nest_SC_' + method + '_' + job_id.to_slug()
        super(SampleClusteringJob, self).__init__(\
            user_id, job_id, userfiles_dir, job_dir_relative_path,
            basename, timeout, cloud,
            'knowengdev/samples_clustering_pipeline:08_02_2017',
            max_num_threads, 15000)

    def get_command(self):
        """Returns the docker command for sample_clustering."""
        return 'date && cd ' + \
            os.path.join(ChronosJob.cloud_path_dict[self.cloud], 'userfiles',\
                self.job_dir_relative_path) + \
            ' && python3 /home/src/samples_clustering.py ' + \
            ' -run_directory ./' + \
            ' -run_file run.yml' + \
            ' && date;'

    def is_ready(self):
        """Returns true iff preprocessing is done."""
        return self.prep_job.is_done()

    def is_done(self):
        """Returns true iff all of the files have been created."""
        return_val = False
        found_target1 = False
        found_target2 = False
        target1_filename_fragment = 'top_genes_by_cluster_'
        target2_filename_fragment = 'clustering_evaluation_result_'
        for name in os.listdir(self.results_dir_path):
            if name.startswith(target1_filename_fragment):
                found_target1 = True
            if name.startswith(target2_filename_fragment):
                found_target2 = True
        return_val = found_target1
        if self.response_file_relative_path is not None:
            return_val = return_val and found_target2
        return return_val

    def on_done(self):
        """Processes scores, loads data to database, prepares zip file, and
        deletes self from Chronos.

            Returns:
                None: None.

        """
        # the exact filenames change with every run, so we'll have to find these
        genes_variance_file_path = None
        genes_average_per_cluster_file_path = None
        samples_label_by_cluster_file_path = None
        consensus_matrix_file_path = None
        genes_by_samples_heatmap_file_path = None
        top_genes_by_cluster_file_path = None
        clustering_evaluation_file_path = None

        for name in os.listdir(self.results_dir_path):
            if name.startswith('genes_variance_'):
                genes_variance_file_path = os.path.join(\
                    self.results_dir_path, name)
            elif name.startswith('genes_averages_by_cluster_'):
                genes_average_per_cluster_file_path = os.path.join(\
                    self.results_dir_path, name)
            elif name.startswith('samples_label_by_cluster_'):
                samples_label_by_cluster_file_path = os.path.join(\
                    self.results_dir_path, name)
            elif name.startswith('consensus_matrix_'):
                consensus_matrix_file_path = os.path.join(\
                    self.results_dir_path, name)
            elif name.startswith('genes_by_samples_heatmap_'):
                genes_by_samples_heatmap_file_path = os.path.join(\
                    self.results_dir_path, name)
            elif name.startswith('top_genes_by_cluster_'):
                top_genes_by_cluster_file_path = os.path.join(\
                    self.results_dir_path, name)
            elif name.startswith('clustering_evaluation_result_'):
                clustering_evaluation_file_path = os.path.join(\
                    self.results_dir_path, name)

        top_genes = self.get_top_genes(genes_variance_file_path,\
            genes_average_per_cluster_file_path, 100)
        samples = self.get_ordered_samples(samples_label_by_cluster_file_path)
        genes_heatmap = self.get_genes_heatmap(\
            genes_by_samples_heatmap_file_path, samples, top_genes['global'])
        samples_heatmap = []
        if consensus_matrix_file_path is not None:
            samples_heatmap = self.get_samples_heatmap(\
                consensus_matrix_file_path, samples)

        phenotypes = []
        if clustering_evaluation_file_path is not None:
            phenotypes = self.get_phenotypes(\
                clustering_evaluation_file_path, samples)

        create_sc_record(self.user_id, self.job_id, top_genes, samples,\
            genes_heatmap, samples_heatmap, phenotypes)

        self.prepare_zip_file(\
            top_genes_by_cluster_file_path, consensus_matrix_file_path,
            samples_label_by_cluster_file_path, clustering_evaluation_file_path,
            genes_average_per_cluster_file_path)
        self.delete_from_chronos()

    def get_top_genes(self, genes_variance_file_path,\
        genes_average_per_cluster_file_path, num_top_genes):
        """Returns a dict capturing top genes per cluster and top genes overall.

        Args:
            genes_variance_file_path (str): The path to the file
                containing the feature variance per gene.
            genes_average_per_cluster_file_path (str): The path to the file
                containing the average feature value per gene by cluster.
            num_top_genes (int): The number of top genes to return per set.

        Returns:
            dict: A dict in which the keys are 'global', 'Cluster_0',
                'Cluster_1', and so on for all of the clusters. Each key maps to
                a list containing the `num_top_genes` sorted by score in
                descending order. The elements in the list are dicts with three
                keys: 'name' (the gene name), 'id' (the gene id), and 'score'
                (the gene's score for the parent list's scope).

        """
        return_val = {}
        # prepare to map gene ids to gene names
        # TODO KNOW-153 this should include ids to names from the interaction
        # network, too. If, for a particular gene id, the kn id->name mapping
        # is different from the user's id->name mapping, we should prefer the
        # user's; i.e., load the interaction network's mapping first and
        # overwrite via `update` with the user's mapping. Then we won't need
        # the `get` on `gene_id_to_name` when assigning the name below.
        gene_id_to_name = get_dict_from_id_to_name(\
            os.path.join(self.userfiles_dir, self.gene_names_map_relative_path))
        # read top genes across clusters
        df_global_genes = pd.read_csv(\
            genes_variance_file_path, delimiter='\t', index_col=0)
        # grab the top `num_top_genes` by score
        # pylint: disable=no-member
        sample = df_global_genes['variance'].sort_values(\
            ascending=False).iloc[0:num_top_genes]
        # pylint: enable=no-member
        return_val['global'] = []
        for gene_id, score in sample.iteritems():
            return_val['global'].append({
                'name': gene_id_to_name.get(gene_id, gene_id),
                'id': gene_id,
                'score': score
            })
        # read top genes per cluster
        df_cluster_genes = pd.read_csv(\
            genes_average_per_cluster_file_path, delimiter='\t', index_col=0)
        # col_names are like 'Cluster_0'
        for col_name in df_cluster_genes:
            col = df_cluster_genes[col_name]
            # grab the top `num_top_genes` by score
            sample = col.sort_values(ascending=False).iloc[0:num_top_genes]
            return_val[col_name] = []
            for gene_id, score in sample.iteritems():
                return_val[col_name].append({
                    'name': gene_id_to_name.get(gene_id, gene_id),
                    'id': gene_id,
                    'score': score
                })
        return return_val

    def get_ordered_samples(self, samples_label_by_cluster_file_path):
        """Returns a list of samples ordered as they should appear as columns
        in the heatmap, from left to right.

        Args:
            samples_label_by_cluster_file_path (str): The path to the file
                containing sample labels with their cluster labels.

        Returns:
            list: A list of dicts, in which each dict has keys `id`, which maps
                to a string, and `cluster`, which maps to an int.

        """
        return_val = None
        with open(samples_label_by_cluster_file_path, 'r') as infile:
            pairs = [row.rstrip().split('\t') for row in infile]
            return_val = [{'id': p[0], 'cluster': int(p[1])} for p in pairs]
        # sort by cluster then by id
        return_val.sort(key=lambda x: (x['cluster'], x['id']))
        return return_val

    def get_genes_heatmap(self, genes_by_samples_heatmap_file_path, samples,\
        top_global_genes):
        """Returns a 2D list (rows of columns) of heatmap values for a
        samples-by-genes heatmap. Columns are ordered according to `samples`.
        Rows are ordered according to `top_global_genes`.

        Args:
            genes_by_samples_heatmap_file_path (str): The path to the file
                containing feature data per sample.
            samples (list): A list as returned by `get_ordered_samples`.
            top_global_genes (list): A list as retrieved by the `global` key
                from the dict returned by `get_top_genes`.

        Returns:
            list: A list of lists of floats.

        """
        df_genes = pd.read_csv(\
            genes_by_samples_heatmap_file_path, delimiter='\t', index_col=0)
        # order rows, discarding those that don't match top_genes
        row_order = [g['id'] for g in top_global_genes]
        # pylint: disable=no-member
        df_genes = df_genes.reindex(row_order)
        # pylint: enable=no-member
        # order columns
        col_order = [s['id'] for s in samples]
        df_genes = df_genes[col_order]
        return df_genes.values.tolist()

    def get_samples_heatmap(self, consensus_matrix_file_path, samples):
        """Returns a 2D list (rows of columns) of heatmap values for a
        samples-by-samples heatmap only shown for consensus clustering. Both
        dimensions are ordered according to `samples`.

        Args:
            consensus_matrix_file_path (str): The path to the file
                containing consensus clustering scores.
            samples (list): A list as returned by `get_ordered_samples`.

        Returns:
            list: A list of lists of floats.

        """
        df_consensus = pd.read_csv(\
            consensus_matrix_file_path, delimiter='\t', index_col=0)
        df_consensus.index = df_consensus.index.map(unicode)
        id_order = [s['id'] for s in samples]
        # order rows
        # pylint: disable=no-member
        df_consensus = df_consensus.reindex(id_order)
        # pylint: enable=no-member
        # order columns
        df_consensus = df_consensus[id_order]
        return df_consensus.values.tolist()

    def get_phenotypes(self, clustering_evaluation_file_path, samples):
        """Returns a list of phenotype data, in which each item is a dictionary
        with keys `name`, `score`, and `values`.

        Args:
            clustering_evaluation_file_path (str): The path to the file
                containing clustering evaluation data.
            samples (list): A list as returned by `get_ordered_samples`.

        Returns:
            list: A list of phenotype data.

        """
        # read phenotypes values
        response_file_path = os.path.join(\
            self.userfiles_dir, self.response_file_relative_path)
        df_phenotypes = pd.read_csv(\
            response_file_path, delimiter='\t', index_col=0)
        df_phenotypes.index = df_phenotypes.index.map(unicode)
        # reorder rows
        id_order = [s['id'] for s in samples]
        # pylint: disable=no-member
        df_phenotypes = df_phenotypes.reindex(id_order)
        # pylint: enable=no-member
        # read pvals
        df_evaluations = pd.read_csv(\
            clustering_evaluation_file_path, delimiter='\t', index_col=0)
        s_pvals = df_evaluations['pval']
        # combine
        return_val = []
        for col in df_phenotypes:
            values = df_phenotypes[col].values.tolist()
            # replace any NaN with None for JSON encoding
            values = [None if (isinstance(v, float) and isnan(v)) else v \
                for v in values]
            return_val.append({
                'name': col,
                'score': s_pvals[col],
                'values': values
            })
        return return_val

    def prepare_zip_file(self, top_genes_by_cluster_file_path, \
        consensus_matrix_file_path, samples_label_by_cluster_file_path, \
        clustering_evaluation_file_path, genes_average_per_cluster_file_path):
        """Creates a zip file on disk for later download by the user.

        Args:
            top_genes_by_cluster_file_path (str): The path to the file
                containing top genes per cluster.
            consensus_matrix_file_path (str): The path to the file
                containing consensus clustering scores.
            samples_label_by_cluster_file_path (str): The path to the file
                containing sample labels with their cluster labels.
            clustering_evaluation_file_path (str): The path to the file
                containing clustering evaluation data.
            genes_average_per_cluster_file_path (str): The path to the file
                containing gene averages per cluster.

        Returns:
            None.

        """
        # need the following:
        # 1. readme
        # 2. cleaned features file
        # 3. gene-name map
        # 4. run yaml
        # 5. interaction network metadata if network
        # 6. samples to clusters
        # 7. samples by samples heatmap
        # 8. gene avg by cluster
        # 9. top genes by cluster
        # 10. cluster evals
        zip_path = os.path.join(\
            self.job_dir_path, 'download.zip')
        with ZipFile(zip_path, 'w', ZIP_DEFLATED) as zipout:

            zipout.write(\
                '/zip_readmes/README-SC.txt', 'README-SC.txt')

            cleaned_features_path = os.path.join(\
                self.userfiles_dir, self.features_file_relative_path)
            zipout.write(\
                cleaned_features_path, 'clean_genomic_matrix.txt')

            gene_names_map_path = os.path.join(\
                self.userfiles_dir, self.gene_names_map_relative_path)
            zipout.write(\
                gene_names_map_path, 'gene_map.txt')

            zipout.write(\
                self.yml_path, 'run_params.yml')

            if self.gg_network_metadata_full_path is not None:
                zipout.write(self.gg_network_metadata_full_path, \
                    'interaction_network.metadata')
            zipout.write(\
                samples_label_by_cluster_file_path,\
                'sample_labels_by_cluster.txt')

            if consensus_matrix_file_path is not None:
                zipout.write(\
                    consensus_matrix_file_path, 'consensus_matrix.txt')

            zipout.write(\
                genes_average_per_cluster_file_path, 'gene_avgs_by_cluster.txt')

            zipout.write(\
                top_genes_by_cluster_file_path, 'top_genes_by_cluster.txt')

            if clustering_evaluation_file_path is not None:
                zipout.write(\
                    clustering_evaluation_file_path, \
                    'clustering_evaluations.txt')

def get_sample_clustering_runners(\
    user_id, job_id, userfiles_dir, project_dir, timeout, cloud, species_id,\
    features_file_id, response_file_id, method, num_clusters, use_network,\
    network_name, network_smoothing, use_bootstrapping, num_bootstraps,\
    bootstrap_sample_percent):
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
        features_file_id (NestId): The NestId of the features file in the database.
        response_file_id (NestID): The NestId of the response file in the database.
        method (str): One of ['K-means'].
        num_clusters (int): The number of clusters to form.
        use_network (bool): Whether to use the knowledge network.
        network_name (str): The network to use when use_network is True.
        network_smoothing (float): The amount of network smoothing to use.
        use_bootstrapping (bool): Whether to use bootstrapping.
        num_bootstraps (int): The number of bootstraps to run.
        bootstrap_sample_percent (float): The percentage of columns to use
            per bootstrap.

    Returns:
        list: A list of ChronosJob instances required to run an SC job.

    """
    job_name = "nest_SC_" + method + '_' + job_id.to_slug()
    job_dir_relative_path = os.path.join(project_dir, job_name)
    os.mkdir(os.path.join(userfiles_dir, job_dir_relative_path))

    features_file_dto = get_file_record(user_id, features_file_id)
    cleaned_features_file_relative_path = \
        get_cleaned_spreadsheet_relative_path(\
            job_dir_relative_path, features_file_dto)

    gene_names_map_relative_path = \
        get_gene_names_map_relative_path(\
            job_dir_relative_path, features_file_dto)

    response_file_dto = None
    response_file_relative_path = None
    if response_file_id is not None:
        response_file_dto = get_file_record(user_id, response_file_id)
        response_file_relative_path = \
            get_cleaned_spreadsheet_relative_path(\
                job_dir_relative_path, response_file_dto)

    gg_network_name_full_path = None
    gg_network_metadata_full_path = None
    if use_network:
        networks = get_merged_network_info('/networks/')
        match = [net for net in networks if \
            net['species_id'] == species_id and \
            net['edge_type_name'] == network_name][0]
        gg_network_name_full_path = '../../../networks/' + match['path_to_edge']
        gg_network_metadata_full_path = '../../../networks/' + \
            match['path_to_metadata']

    prep_job = DataCleanupJob(\
        user_id, job_id, userfiles_dir, timeout, cloud, species_id,
        features_file_dto, response_file_dto, gg_network_name_full_path,
        job_dir_relative_path, PipelineType.SAMPLE_CLUSTERING, None)
    return [
        prep_job,
        SampleClusteringJob(\
            user_id, job_id, userfiles_dir, job_dir_relative_path, timeout,
            cloud, cleaned_features_file_relative_path,
            gene_names_map_relative_path, response_file_relative_path,
            method, num_clusters, gg_network_name_full_path,
            gg_network_metadata_full_path, network_smoothing,
            use_bootstrapping, num_bootstraps, bootstrap_sample_percent,
            prep_job)
    ]

# TODO make data model v1.0
# here's alpha:
# {
#     // TODO more compact representation; would help to know how much overlap
#     // exists between clusters
#     topGenes: {
#         global: [{id, name, score}],
#         Cluster_0: [{id, name, score}],
#         ...
#     },
#     // ordered for heatmap columns, left to right
#     samples: [{id: string, cluster: int}],
#     // rows of columns, ordered to match `samples` and `topGenes.global`
#     genes_heatmap: float[][],
#     // rows of columns, for bootstrapped runs only, ordered to match `samples`
#     samples_heatmap: float[][],
#     phenotypes: [{
#         name: string,
#         score: float,
#         values: any[] // ordered to match `samples`
#     }]
# }
