import 'rxjs/add/observable/forkJoin';
import {Observable} from 'rxjs/Observable';
import {Subject} from 'rxjs/Subject';
import {Subscription} from 'rxjs/Subscription';

import {HelpContent, HelpContentGroup, HelpContentElement, HelpElementType} from '../HelpContent';
import {Form, FormGroup, FormField, BooleanFormField, HiddenFormField, SelectFormField, SelectOption, FileFormField, DoubleFileFormField, NumberFormField,
    NumberType, NumberFormFieldSlider, SLIDER_NONE, SLIDER_NO_LABELS, VALID_UNLESS_REQUIRED_BUT_EMPTY, VALID_NUMBER, ALWAYS, IF} from '../Form';
import {Pipeline} from '../Pipeline';
import {getInteractionNetworkOptions} from './PipelineUtils';
import {AnalysisNetwork, Species} from '../KnowledgeNetwork';
import {FileService} from '../../../services/knoweng/FileService';

export class SampleClusteringPipeline extends Pipeline {
    
    private form = new Subject<Form>();

    constructor(
        private fileService: FileService,
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
                let featuresFileFields: FormField[] = [];

                // create subscription to populate arrays
                let joinedStream: Observable<any[]> = Observable.forkJoin(
                    speciesStream, networksStream);
                let joinedStreamSubscription = joinedStream.subscribe(
                    (joinedArray: any[]) => {
                        // unpack data: first array will be species, second array will be networks
                        let species: Species[] = joinedArray[0];
                        let networks: AnalysisNetwork[] = joinedArray[1];
                        // populate arrays
                        speciesOptions = species.sort((a, b) => d3.ascending(a.display_order, b.display_order)).map(s => new SelectOption(s.name + " (" + s.short_latin_name + ")", s.species_number, s.selected_by_default, s.group_name));
                        Array.prototype.push.apply(featuresFileFields, [
                            new SelectFormField("species", null, "1", "Select species", "Species", true, speciesOptions, false, VALID_UNLESS_REQUIRED_BUT_EMPTY, ALWAYS),
                            new FileFormField("features_file", null, "2", "Select \"omics\" features file", "Features File", true, null, this.fileService, true, false, VALID_UNLESS_REQUIRED_BUT_EMPTY, ALWAYS)
                        ]);
                        
                        networkFields.push(
                            new BooleanFormField("use_network", "Do you want to use the Knowledge Network?", null, null, "Use Network", true, null, VALID_UNLESS_REQUIRED_BUT_EMPTY, ALWAYS)
                        );
                        getInteractionNetworkOptions(species, networks).forEach(nf => {
                            networkFields.push(nf);
                        });
                        networkFields.push(
                            new NumberFormField("network_smoothing", null, "2", "Choose the amount of network smoothing", "Network Smoothing", true, 50, NumberType.FLOAT, true, 0, 100, new NumberFormFieldSlider("data driven", "network driven"), VALID_NUMBER, IF('use_network', true))
                        );
                        
                        this.form.next(new Form("sample_clustering", [
                            new FormGroup("Features File", SAMPLE_CLUSTERING_FEATURES_FILE_HELP_CONTENT, featuresFileFields),
                            new FormGroup("Response File", SAMPLE_CLUSTERING_RESPONSE_FILE_HELP_CONTENT, [
                                new FileFormField("response_file", null, null, "Select phenotype file", "Response File", false, null, this.fileService, false, false, VALID_UNLESS_REQUIRED_BUT_EMPTY, ALWAYS)
                            ]),
                            new FormGroup("Parameters", SAMPLE_CLUSTERING_PARAMETERS_HELP_CONTENT, [
                                new SelectFormField("method", null, "1", "Select the final clustering algorithm to use", "Method", true, [
                                    new SelectOption("K-Means", "K-means", true) // TODO revisit when real choices available and they sort out initial clustering vs. final clustering; this may need to move to the bootstrapping page because it'd be constrained
                                    ], false, VALID_UNLESS_REQUIRED_BUT_EMPTY, ALWAYS),
                                new NumberFormField("num_clusters", null, "2", "Enter the number of clusters you wish the analysis to return", "# Clusters", true, 5, NumberType.INTEGER, false, 2, 20, SLIDER_NONE, VALID_NUMBER, ALWAYS)
                            ]),
                            new FormGroup("Network", SAMPLE_CLUSTERING_NETWORK_HELP_CONTENT, networkFields),
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

var SAMPLE_CLUSTERING_ABOUT = "You have a spreadsheet that contains gene-based &ldquo;omics&rdquo; data signatures of multiple biological samples. You want to find clusters of the samples that have specific genomic signatures (e.g. subtypes of cancer patients). You may also have phenotypic measurements (e.g., drug response, patient survival, etc.) for each sample. In this case, you want to find genomic subtypes related to the important phenotypic measurements. This pipeline uses different clustering algorithms to group the samples and scores the clusters in relation to the provided phenotypes. This pipeline also provides methods for finding robust clusters and/or using the Knowledge Network to transform the genomic signatures of the samples.";

var SAMPLE_CLUSTERING_TRAINING = new HelpContentGroup("Info and training", [
    new HelpContentElement("Quickstart Guide", HelpElementType.HEADING),
    new HelpContentElement("This guide walks you through the entire pipeline from setup to visualization of results. It also includes links to sample data.", HelpElementType.BODY),
    new HelpContentElement("<a href='//www.knoweng.org/quick-start/' target='_blank'>Download the Sample Clustering Quickstart Guide PDF</a>", HelpElementType.BODY),
    new HelpContentElement("Video Tutorials", HelpElementType.HEADING),
    new HelpContentElement("The KnowEnG YouTube Channel contains videos for every pipeline (some currently in development) as well as information about unique attributes of the KnowEnG Platform.", HelpElementType.BODY),
    new HelpContentElement("<a href='//www.youtube.com/channel/UCjyIIolCaZIGtZC20XLBOyg' target='_blank'>Visit the KnowEnG YouTube Channel</a>", HelpElementType.BODY)
]);

var SAMPLE_CLUSTERING_OVERVIEW_HELP_CONTENT = new HelpContent([
    new HelpContentGroup("About Sample Clustering", [
        new HelpContentElement(SAMPLE_CLUSTERING_ABOUT, HelpElementType.BODY)
    ]),
    new HelpContentGroup("How does this pipeline work?", [
        new HelpContentElement("This pipeline takes a genomic spreadsheet that represents each biological sample in the collection as a profile of genomic measurements. It calculates the similarity of the profiles and clusters the samples into a requested number of subtypes. If the user supplied phenotypic data for the samples, the pipeline uses standard statistical tests to identify if the discovered subtypes correlate with any phenotypes.", HelpElementType.BODY)
    ]),
    new HelpContentGroup("How does this pipeline differ from standard clustering?", [
        new HelpContentElement("We have incorporated into this pipeline the advanced features of the Network-based Stratification method from (<a href='//www.ncbi.nlm.nih.gov/pubmed/24037242' target='_blank'>Hofree, et al.</a>). These features include a spreadsheet sampling procedure that repeatedly clusters a subset of the user data and then robustly identifies the subtypes from the overall consensus. The pipeline also has the ability to smooth/transform the genomic measurements in order to incorporate prior knowledge of protein interactions and relationships. Samples with the same pathways affected may show greater similarity with their transformed genomic signatures and may cluster into more accurate subtypes.", HelpElementType.BODY)
    ]),
    new HelpContentGroup("What input does the pipeline need?", [
        new HelpContentElement("A &ldquo;genomic features file&rdquo; that contains a spreadsheet of &ldquo;omics&rdquo; data, with rows for genes and columns for samples. The values of the spreadsheet must be non-negative and could indicate genes in the sample that are differentially expressed, have somatic mutations, or are near regions of open chromatin, etc.", HelpElementType.BODY),
        new HelpContentElement("Optionally, a &ldquo;response file&rdquo; that contains a spreadsheet of phenotypic data, with rows for each sample and columns for each phenotype.", HelpElementType.BODY)
    ]),
    new HelpContentGroup("What output does the pipeline produce?", [
        new HelpContentElement("Primarily, the pipeline output assigns each sample to one of several discovered genomic subtypes/clusters. The visualization will also allow you to explore the average genomic signature of each subtype and, if phenotypic information was supplied, the relationships between phenotypes and the subtypes.", HelpElementType.BODY)
    ]),
    SAMPLE_CLUSTERING_TRAINING
]);

var SAMPLE_CLUSTERING_FEATURES_FILE_HELP_CONTENT = new HelpContent([
    new HelpContentGroup("What is the &ldquo;&lsquo;omics&rsquo; feature file&rdquo;?", [
        new HelpContentElement("This file is the tab-separated spreadsheet with gene-level &ldquo;omics&rdquo; profiles of your collection of samples. The rows of the spreadsheet must represent genes and its columns represent samples. The first (header) row should contain the sample identifiers for the corresponding column. The first column of the spreadsheet should be the gene identifiers corresponding to each row. The values should be non-negative (e.g. sequencing scores from transcriptomic or epigenomic experiments) or binary (e.g. differential expression or somatic mutations indicators). NAs in this spreadsheet are currently not supported.", HelpElementType.BODY)
    ]),
    new HelpContentGroup("Acceptable Data Formats", [
        new HelpContentElement("Spreadsheets may be loaded as tab-separated files.", HelpElementType.BODY)
    ]),
    SAMPLE_CLUSTERING_TRAINING
]);

var SAMPLE_CLUSTERING_RESPONSE_FILE_HELP_CONTENT = new HelpContent([
    new HelpContentGroup("What is the &ldquo;phenotype file&rdquo;?", [
        new HelpContentElement("This is the tab-separated spreadsheet file with phenotype values, one for each sample. It must contain rows for each sample and columns for each phenotype. The names of the samples must be identical to those in the genomic feature file for cluster evaluation. NAs are allowed as phenotype values.", HelpElementType.BODY)
    ]),
    new HelpContentGroup("Acceptable Data Formats", [
        new HelpContentElement("Spreadsheets may be loaded as tab-separated files.", HelpElementType.BODY)
    ]),
    SAMPLE_CLUSTERING_TRAINING
]);

var SAMPLE_CLUSTERING_PARAMETERS_HELP_CONTENT = new HelpContent([
    new HelpContentGroup("What is the &ldquo;final clustering algorithm&rdquo;?", [
        new HelpContentElement("There are many methods for grouping samples into clusters/subtypes. These methods are applied to the final network-transformed or bootstrap-aggregated data depending on the values of the other pipeline options.", HelpElementType.BODY),
        new HelpContentElement("K-Means", HelpElementType.HEADING),
        new HelpContentElement("This is an iterative clustering method that attempts to find a clustering assignment that minimizes the distance of the samples to the cluster center.", HelpElementType.BODY)
    ]),
    /*
    new HelpContentGroup("Method 1: K-Means", [
        new HelpContentElement("About", HelpElementType.HEADING),
        new HelpContentElement("This is an iterative clustering method that attempts to find a clustering assignment that minimizes the distance of the samples to the cluster center.", HelpElementType.BODY)
    ]),
    */
    new HelpContentGroup("Number of Clusters", [
        new HelpContentElement("The number of clusters/subtypes is an important parameter that specifies how many groups the samples will be partitioned into. This parameter can be set for between 2 and 20 clusters. Poor results may indicate an inappropriate choice for this parameter.", HelpElementType.BODY)
    ]),
    SAMPLE_CLUSTERING_TRAINING
]);

var SAMPLE_CLUSTERING_NETWORK_HELP_CONTENT = new HelpContent([
    new HelpContentGroup("What does it mean to use the Knowledge Network?", [
        new HelpContentElement("Briefly, the network makes use of known relationships such as protein-protein interactions, genetic interactions and homology relationships among genes. These relationships enable the pipeline to transform the genomic signatures of each sample by integrating each gene's signal with the signals from its interacting neighbors. This transformation can potentially aid in the correct clustering of samples by propagating weak individual gene signals to higher levels (pathways and modules) where the sample similarity is stronger. ", HelpElementType.BODY)
    ]),
    new HelpContentGroup("Advantages", [
        new HelpContentElement("One major advantage of using the Knowledge Network was shown in <a href='//www.ncbi.nlm.nih.gov/pubmed/24037242' target='_blank'>Hofree, et al.</a> on finding genomic subtypes from somatic mutation data. They demonstrated that incorporating interactions from the Knowledge Network was able to transform difficult to cluster sparse genomic profiles into more readily clustered signatures. In their work, each cancer sample has very few genes with somatic mutations and therefore the genomic profiles are very sparse. The samples are found not to be similar because they do not have shared genes that are mutated. Interactions in the Knowledge Network were used to compute the mutation signature across gene neighborhoods (pathways, modules) and that level sample similarity can be detected and used to produce meaningful subtypes.", HelpElementType.BODY)
    ]),
    new HelpContentGroup("Disadvantages", [
        new HelpContentElement("This is a novel approach to sample clustering. It is far more common to perform clustering on the original data. It is not clear that incorporating interactions in the Knowledge Network will not add noise to the genomic signatures that underperform clustering on the original data.", HelpElementType.BODY)
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
