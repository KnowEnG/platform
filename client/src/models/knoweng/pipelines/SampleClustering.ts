import 'rxjs/add/observable/forkJoin';
import {Observable} from 'rxjs/Observable';
import {Subject} from 'rxjs/Subject';
import {Subscription} from 'rxjs/Subscription';

import {HelpContent, HelpContentGroup, HelpContentElement, HelpElementType} from '../HelpContent';
import {Form, FormGroup, FormField, BooleanFormField, HiddenFormField, SelectFormField, SelectOption, FileFormField, DoubleFileFormField, NumberFormField,
    NumberType, NumberFormFieldSlider, SLIDER_NONE, SLIDER_NO_LABELS, VALID_UNLESS_REQUIRED_BUT_EMPTY, VALID_NUMBER, ALWAYS, IF, AND, OR} from '../Form';
import {Pipeline} from '../Pipeline';
import {getInteractionNetworkOptions} from './PipelineUtils';
import {AnalysisNetwork, Species} from '../KnowledgeNetwork';
import {FileService} from '../../../services/knoweng/FileService';
import {JobService} from '../../../services/knoweng/JobService';

export class SampleClusteringPipeline extends Pipeline {

    private form = new Subject<Form>();

    constructor(
        private fileService: FileService,
        private jobService: JobService,
        speciesStream: Observable<Species[]>,
        networksStream: Observable<AnalysisNetwork[]>) {

        super(
            "Sample Clustering",
            "sample_clustering",
            SAMPLE_CLUSTERING_ABOUT,
            SAMPLE_CLUSTERING_OVERVIEW_HELP_CONTENT,
            () => {
                // initialize kn-dependent data to empty arrays
                let speciesOptions: SelectOption[] = [];
                let networkFields: FormField[] = [];

                // create subscription to populate arrays
                let joinedStream: Observable<any[]> = Observable.forkJoin(
                    speciesStream, networksStream);
                let joinedStreamSubscription = joinedStream.subscribe(
                    (joinedArray: any[]) => {
                        // unpack data: first array will be species, second array will be networks
                        let species: Species[] = joinedArray[0];
                        let networks: AnalysisNetwork[] = joinedArray[1];

                        // populate arrays

                        networkFields.push(
                            new BooleanFormField("use_network", "Do you want to use the Knowledge Network?", null, null, "Use Network", true, null, VALID_UNLESS_REQUIRED_BUT_EMPTY, ALWAYS)
                        );
                        // species
                        speciesOptions = species.sort((a, b) => d3.ascending(a.display_order, b.display_order)).map(s => new SelectOption(s.name + " (" + s.short_latin_name + ")", s.species_number, s.selected_by_default, s.group_name));
                        networkFields.push(
                            new SelectFormField("species", null, "1", "Select species", "Species", true, speciesOptions, false, VALID_UNLESS_REQUIRED_BUT_EMPTY, IF('use_network', true))
                        );
                        // interaction networks
                        getInteractionNetworkOptions(species, networks, "2").forEach(nf => {
                            networkFields.push(nf);
                        });
                        networkFields.push(
                            new NumberFormField("network_smoothing", null, "3", "Choose the amount of network smoothing", "Network Smoothing", true, 50, NumberType.FLOAT, true, 0, 100, new NumberFormFieldSlider("data driven", "network driven"), VALID_NUMBER, IF('use_network', true))
                        );

                        this.form.next(new Form("sample_clustering", [
                            new FormGroup("Features File", SAMPLE_CLUSTERING_FEATURES_FILE_HELP_CONTENT, [
                                new FileFormField("features_file", null, null, "Select \"omics\" features file", "Features File", true, null, this.fileService, this.jobService, true, false, VALID_UNLESS_REQUIRED_BUT_EMPTY, ALWAYS)
                            ]),
                            new FormGroup("Response File", SAMPLE_CLUSTERING_RESPONSE_FILE_HELP_CONTENT, [
                                new FileFormField("response_file", null, null, "Select phenotype file", "Response File", false, null, this.fileService, this.jobService, false, false, VALID_UNLESS_REQUIRED_BUT_EMPTY, ALWAYS)
                            ]),
                            new FormGroup("Network", SAMPLE_CLUSTERING_NETWORK_HELP_CONTENT, networkFields),
                            new FormGroup("Parameters", SAMPLE_CLUSTERING_PARAMETERS_HELP_CONTENT, [
                                new NumberFormField("num_clusters", null, null, "Enter the number of clusters you wish the analysis to return", "# Clusters", true, 5, NumberType.INTEGER, false, 2, 15, SLIDER_NONE, VALID_NUMBER, IF('use_network', true)),
                                new NumberFormField("num_clusters", null, "1", "Enter the number of clusters you wish the analysis to return", "# Clusters", true, 5, NumberType.INTEGER, false, 2, 15, SLIDER_NONE, VALID_NUMBER, IF('use_network', false)),
                                new HiddenFormField("method", "K-means", IF('use_network', true)),
                                new SelectFormField("method", null, "2", "Select the clustering algorithm to use", "Method", true, [
                                    new SelectOption("K-Means", "K-means", true),
                                    new SelectOption("Hierarchical", "Hierarchical", false)
                                    ], false, VALID_UNLESS_REQUIRED_BUT_EMPTY, IF('use_network', false)),
                                // affinity metric for hierarchical
                                new SelectFormField("affinity_metric", null, "3", "Select the affinity metric to use", "Affinity Metric", true, [
                                    new SelectOption("Euclidean", "euclidean", true),
                                    new SelectOption("Manhattan", "manhattan", false),
                                    new SelectOption("Jaccard", "jaccard", false)
                                    ], false, VALID_UNLESS_REQUIRED_BUT_EMPTY, IF('method', 'Hierarchical')),
                                // linkage criterion for hierarchical clustering
                                // three cases:
                                // 1. if affinity metric == euclidean, options are average/complete/ward
                                // 2. if affinity metric == manhattan, options are average/complete
                                // 3. if affinity metric == jaccard, only ward works
                                new SelectFormField("linkage_criterion", null, "4", "Select the linkage criterion to use", "Linkage Criterion", true, [
                                    new SelectOption("Average", "average", false),
                                    new SelectOption("Complete", "complete", false),
                                    new SelectOption("Ward", "ward", true)
                                    ], false, VALID_UNLESS_REQUIRED_BUT_EMPTY, IF('affinity_metric', 'euclidean')),
                                new SelectFormField("linkage_criterion", null, "4", "Select the linkage criterion to use", "Linkage Criterion", true, [
                                    new SelectOption("Average", "average", true),
                                    new SelectOption("Complete", "complete", false)
                                    ], false, VALID_UNLESS_REQUIRED_BUT_EMPTY, IF('affinity_metric', 'manhattan')),
                                new HiddenFormField("linkage_criterion", "ward", IF('affinity_metric', 'jaccard'))
                            ]),
                            new FormGroup("Bootstrapping", SAMPLE_CLUSTERING_BOOTSTRAPPING_HELP_CONTENT, [
                                new BooleanFormField("use_bootstrapping", "Do you want to use bootstrapping?", null, null, "Use Bootstrapping", true, null, VALID_UNLESS_REQUIRED_BUT_EMPTY, ALWAYS),
                                new NumberFormField("num_bootstraps", null, "1", "Enter the number of bootstraps to use in your analysis", "# Bootstraps", true, 8, NumberType.INTEGER, false, 1, 200, SLIDER_NONE, VALID_NUMBER, IF('use_bootstrapping', true)),
                                new NumberFormField("bootstrap_sample_percent", null, "2", "Enter the bootstrap sample percent", "Sample %", true, 80, NumberType.FLOAT, true, 0, 100, SLIDER_NO_LABELS, VALID_NUMBER, IF('use_bootstrapping', true)),
                                new HiddenFormField("cloud", "aws", ALWAYS)
                            //remove cloud hidden field, too
                            //]),
                            //new FormGroup("Cloud", SAMPLE_HELP_CONTENT, [
                            //    new SelectFormField("cloud", "Choose a cloud computing resource.", null, "Select a cloud computing resource on which to run your analysis", "Cloud", true, [
                            //        new SelectOption("Amazon", "aws", true, ALWAYS)
                            //        ], false, VALID_UNLESS_REQUIRED_BUT_EMPTY, ALWAYS)
                            ])
                        ]));

                        joinedStreamSubscription.unsubscribe();
                    }
                );

                return this.form.asObservable();
            }
        );
    }
}

var SAMPLE_CLUSTERING_ABOUT = "You have a spreadsheet that contains &ldquo;omics&rdquo; data signatures of multiple biological samples. You want to find clusters of the samples that have specific &ldquo;omics&rdquo; signatures (e.g. subtypes of cancer patients). You may also have phenotypic measurements (e.g., drug response, patient survival, etc.) for each sample. In this case, you want to find &ldquo;omics&rdquo; subtypes related to the important phenotypic measurements. This pipeline uses different clustering algorithms to group the samples and scores the clusters in relation to the provided phenotypes. This pipeline also provides methods for finding robust clusters and/or using the Knowledge Network to transform the genomic signatures of the samples, if the features are genes.";

var SAMPLE_CLUSTERING_TRAINING = new HelpContentGroup("Info and training", [
    new HelpContentElement("Quickstart Guide", HelpElementType.HEADING),
    new HelpContentElement("This guide walks you through the entire pipeline from setup to visualization of results. It also includes links to sample data.", HelpElementType.BODY),
    new HelpContentElement("<a href='https://knoweng.org/quick-start/' target='_blank'>Download the Sample Clustering Quickstart Guide PDF</a>", HelpElementType.BODY),
    new HelpContentElement("Video Tutorials", HelpElementType.HEADING),
    new HelpContentElement("The KnowEnG YouTube Channel contains videos for every pipeline (some currently in development) as well as information about unique attributes of the KnowEnG Platform.", HelpElementType.BODY),
    new HelpContentElement("<a href='https://www.youtube.com/channel/UCjyIIolCaZIGtZC20XLBOyg' target='_blank'>Visit the KnowEnG YouTube Channel</a>", HelpElementType.BODY)
]);

var SAMPLE_CLUSTERING_OVERVIEW_HELP_CONTENT = new HelpContent([
    new HelpContentGroup("About Sample Clustering", [
        new HelpContentElement(SAMPLE_CLUSTERING_ABOUT, HelpElementType.BODY)
    ]),
    new HelpContentGroup("How does this pipeline work?", [
        new HelpContentElement("This pipeline takes a features spreadsheet that represents each biological sample in the collection as a profile of &ldquo;omics&rdquo; measurements. It calculates the similarity of the profiles and clusters the samples into a requested number of subtypes. If the user supplied phenotypic data for the samples, the pipeline uses standard statistical tests to identify if the discovered subtypes correlate with any phenotypes.", HelpElementType.BODY)
    ]),
    new HelpContentGroup("How does this pipeline differ from standard clustering?", [
        new HelpContentElement("We have incorporated into this pipeline the advanced features of the Network-based Stratification method from (<a href='https://www.ncbi.nlm.nih.gov/pubmed/24037242' target='_blank'>Hofree, et al.</a>). These features include a spreadsheet sampling procedure that repeatedly clusters a subset of the user data and then robustly identifies the subtypes from the overall consensus. The pipeline also has the ability to smooth/transform genomic features in order to incorporate prior knowledge of protein interactions and relationships. Samples with the same pathways affected may show greater similarity with their transformed genomic signatures and may cluster into more accurate subtypes.", HelpElementType.BODY)
    ]),
    new HelpContentGroup("What input does the pipeline need?", [
        new HelpContentElement("A &ldquo;features file&rdquo; that contains a spreadsheet of &ldquo;omics&rdquo; data, with rows for features and columns for samples. The values of the spreadsheet must be non-negative and in the case of genetic features could indicate genes in the sample that are differentially expressed, have somatic mutations, or are near regions of open chromatin, etc.", HelpElementType.BODY),
        new HelpContentElement("Optionally, a &ldquo;response file&rdquo; that contains a spreadsheet of phenotypic data, with rows for each sample and columns for each phenotype.", HelpElementType.BODY)
    ]),
    new HelpContentGroup("What output does the pipeline produce?", [
        new HelpContentElement("Primarily, the pipeline output assigns each sample to one of several discovered subtypes/clusters. The visualization will also allow you to explore the average &ldquo;omic&rdquo; signature of each subtype and, if phenotypic information was supplied, the relationships between phenotypes and the subtypes.", HelpElementType.BODY)
    ]),
    SAMPLE_CLUSTERING_TRAINING
]);

var SAMPLE_CLUSTERING_FEATURES_FILE_HELP_CONTENT = new HelpContent([
    new HelpContentGroup("What is the &ldquo;&lsquo;omics&rsquo; features file&rdquo;?", [
        new HelpContentElement("This file is the tab-separated spreadsheet with &ldquo;omics&rdquo; profiles of your collection of samples. The rows of the spreadsheet must represent features and its columns represent samples. The first (header) row should contain the sample identifiers for the corresponding column. The first column of the spreadsheet should be the feature identifiers corresponding to each row. The values should be non-negative (e.g. sequencing scores from transcriptomic or epigenomic experiments) or binary (e.g. differential expression or somatic mutations indicators). NAs in this spreadsheet are currently not supported.", HelpElementType.BODY)
    ]),
    new HelpContentGroup("Acceptable Data Formats", [
        new HelpContentElement("Spreadsheets may be loaded as tab-separated files.", HelpElementType.BODY)
    ]),
    SAMPLE_CLUSTERING_TRAINING
]);

var SAMPLE_CLUSTERING_RESPONSE_FILE_HELP_CONTENT = new HelpContent([
    new HelpContentGroup("What is the &ldquo;phenotype file&rdquo;?", [
        new HelpContentElement("This is the tab-separated spreadsheet file with phenotype values, one for each sample. It must contain rows for each sample and columns for each phenotype. The names of the samples must be identical to those in the features file for cluster evaluation. NAs are allowed as phenotype values.", HelpElementType.BODY)
    ]),
    new HelpContentGroup("Acceptable Data Formats", [
        new HelpContentElement("Spreadsheets may be loaded as tab-separated files.", HelpElementType.BODY)
    ]),
    SAMPLE_CLUSTERING_TRAINING
]);

var SAMPLE_CLUSTERING_PARAMETERS_HELP_CONTENT = new HelpContent([
    new HelpContentGroup("Number of Clusters", [
        new HelpContentElement("The number of clusters/subtypes is an important parameter that specifies how many groups the samples will be partitioned into. This parameter can be set for between 2 and 20 clusters. Poor results may indicate an inappropriate choice for this parameter.", HelpElementType.BODY)
    ]),
    new HelpContentGroup("What is the clustering algorithm?", [
        new HelpContentElement("There are many methods for grouping samples into clusters/subtypes. If you are not using the Knowledge Network, you can select from two methods.", HelpElementType.BODY),
        new HelpContentElement("K-Means", HelpElementType.HEADING),
        new HelpContentElement("This is an iterative clustering method that attempts to find a clustering assignment that minimizes the distance of the samples to the cluster center.", HelpElementType.BODY),
        new HelpContentElement("Hierarchical", HelpElementType.HEADING),
        new HelpContentElement("This is a bottom-up clustering method that initially assigns each sample to its own cluster and iteratively merges similar clusters until it arrives at the desired cluster count.", HelpElementType.BODY),
    ]),
    new HelpContentGroup("Affinity Metric", [
        new HelpContentElement("If you are using hierarchical clustering, you can choose the affinity metric, which determines how distances between samples are measured.", HelpElementType.BODY),
        new HelpContentElement("Euclidean", HelpElementType.HEADING),
        new HelpContentElement("This is the l2 distance between samples.", HelpElementType.BODY),
        new HelpContentElement("Jaccard", HelpElementType.HEADING),
        new HelpContentElement("This is the Jaccard-Needham dissimilarity. It is recommended for, and only compatible with, boolean features.", HelpElementType.BODY),
        new HelpContentElement("Manhattan", HelpElementType.HEADING),
        new HelpContentElement("This is the l1 distance between samples. It can be a good choice if many of the features are zero.", HelpElementType.BODY)
    ]),
    new HelpContentGroup("Linkage Criterion", [
        new HelpContentElement("If you are using hierarchical clustering, depending on the affinity metric selected, you might be able to choose the linkage criterion. The linkage criterion determines how clusters are compared to each other as the algorithm evaluates potential merges.", HelpElementType.BODY),
        new HelpContentElement("Average", HelpElementType.HEADING),
        new HelpContentElement("Average minimizes the average of the distances between all observations of pairs of clusters.", HelpElementType.BODY),
        new HelpContentElement("Complete", HelpElementType.HEADING),
        new HelpContentElement("Complete minimizes the maximum distance between observations of pairs of cluster and can produce clusterings in which the clusters have very different sizes.", HelpElementType.BODY),
        new HelpContentElement("Ward", HelpElementType.HEADING),
        new HelpContentElement("Ward minimizes the sum of squared differences within all clusters and tends to produce evenly-sized clusters.", HelpElementType.BODY)
    ]),
    SAMPLE_CLUSTERING_TRAINING
]);

var SAMPLE_CLUSTERING_NETWORK_HELP_CONTENT = new HelpContent([
    new HelpContentGroup("What does it mean to use the Knowledge Network?", [
        new HelpContentElement("Briefly, if the features are genes, the network makes use of known relationships such as protein-protein interactions, genetic interactions and homology relationships among genes. These relationships enable the pipeline to transform the genomic signatures of each sample by integrating each gene's signal with the signals from its interacting neighbors. This transformation can potentially aid in the correct clustering of samples by propagating weak individual gene signals to higher levels (pathways and modules) where the sample similarity is stronger. ", HelpElementType.BODY)
    ]),
    new HelpContentGroup("Advantages", [
        new HelpContentElement("One major advantage of using the Knowledge Network was shown in <a href='https://www.ncbi.nlm.nih.gov/pubmed/24037242' target='_blank'>Hofree, et al.</a> on finding genomic subtypes from somatic mutation data. They demonstrated that incorporating interactions from the Knowledge Network was able to transform difficult to cluster sparse genomic profiles into more readily clustered signatures. In their work, each cancer sample has very few genes with somatic mutations and therefore the genomic profiles are very sparse. The samples are found not to be similar because they do not have shared genes that are mutated. Interactions in the Knowledge Network were used to compute the mutation signature across gene neighborhoods (pathways, modules) and that level sample similarity can be detected and used to produce meaningful subtypes.", HelpElementType.BODY)
    ]),
    new HelpContentGroup("Disadvantages", [
        new HelpContentElement("This is a novel approach to sample clustering. It is far more common to perform clustering on the original data. It is not clear that incorporating interactions in the Knowledge Network will not add noise to the genomic signatures that underperform clustering on the original data.", HelpElementType.BODY)
    ]),
    new HelpContentGroup("What if my data's species isn't an option in the list?", [
        new HelpContentElement("If your data's species isn't in the list, the Knowledge Network does not contain sufficient data about the species to perform a Knowledge Network-guided analysis. In this case, you should choose not to use the Knowledge Network.", HelpElementType.BODY)
    ]),
    new HelpContentGroup("What is an Interaction Network?", [
        new HelpContentElement("An interaction network represents prior knowledge about a particular type of gene/protein relationships (such as protein-protein physical interactions, genetic interactions, co-expression relationships, etc.). Each network has genes as nodes and its edges represent relationships of a particular type. You may choose which type of relationships to include in the interaction network used in the pipeline.", HelpElementType.BODY)
    ]),
    new HelpContentGroup("What is Network Smoothing?", [
        new HelpContentElement("Network smoothing determines the amount of influence the interactions from the Knowledge Network have on transforming the genomic signature. 0% network smoothing does not transform the original data at all. 100% network smoothing only uses the interactions of the network and ignores the original signature values. Most often, the network influence is set to a value between 40% and 60% and the results are typically stable within that range.", HelpElementType.BODY)
    ]),
    SAMPLE_CLUSTERING_TRAINING
]);

var SAMPLE_CLUSTERING_BOOTSTRAPPING_HELP_CONTENT = new HelpContent([
    new HelpContentGroup("What is bootstrapping?", [
        new HelpContentElement("In this pipeline, bootstrapping or bootstrap sampling is used by performing the network smoothing and clustering on many randomly selected (with replacement) subsets of biological samples. The pipeline keeps track of how often pairs of biological samples are clustered together across all bootstrap samples in an aggregate consensus matrix. The final cluster assignment of the biological samples is found by clustering the consensus matrix.", HelpElementType.BODY)
    ]),
    new HelpContentGroup("How should I choose the number of bootstraps?", [
        new HelpContentElement("Bootstrap sampling is used to obtain a more robust clustering, and more bootstraps can obtain more robust results. However, a large value (up to 200) will increase the computational cost and the amount of time it takes for the results to be ready.", HelpElementType.BODY)
    ]),
    new HelpContentGroup("How should I choose the bootstrap sample percentage?", [
        new HelpContentElement("If the number of bootstraps is larger than 1, you should choose a percentage less than 100. Most often, sample percentage (amount of data to include in each bootstrap) is set to a value between 60% and 90%.", HelpElementType.BODY)
    ]),
    SAMPLE_CLUSTERING_TRAINING
]);
