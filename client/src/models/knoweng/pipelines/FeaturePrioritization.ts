import 'rxjs/add/observable/forkJoin';
import {Observable} from 'rxjs/Observable';
import { Subject }    from 'rxjs/Subject';
import {Subscription} from 'rxjs/Subscription';

import {HelpContent, HelpContentGroup, HelpContentElement, HelpElementType} from '../HelpContent';
import {Form, FormGroup, FormField, BooleanFormField, HiddenFormField, SelectFormField, SelectOption, FileFormField, DoubleFileFormField,
    NumberFormField, NumberType, NumberFormFieldSlider, SLIDER_NONE, SLIDER_NO_LABELS, VALID_UNLESS_REQUIRED_BUT_EMPTY, VALID_NUMBER, ALWAYS, AND, OR, IF} from '../Form';
import {Pipeline} from '../Pipeline';
import {getInteractionNetworkOptions} from './PipelineUtils';
import {AnalysisNetwork, Species} from '../KnowledgeNetwork';
import {FileService} from '../../../services/knoweng/FileService';
import {JobService} from '../../../services/knoweng/JobService';

export class FeaturePrioritizationPipeline extends Pipeline {
    
    private form = new Subject<Form>();

    constructor(
        private fileService: FileService,
        private jobService: JobService,
        speciesStream: Observable<Species[]>,
        networksStream: Observable<AnalysisNetwork[]>) {
            
        super(
            "Feature Prioritization",
            "feature_prioritization",
            FEATURE_PRIORITIZATION_ABOUT,
            FEATURE_PRIORITIZATION_OVERVIEW_HELP_CONTENT,
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
                            new NumberFormField("network_influence", null, "3", "Choose amount of network influence", "Network Influence", true, 50, NumberType.FLOAT, true, 0, 100, new NumberFormFieldSlider("data driven", "network driven"), VALID_NUMBER, IF('use_network', true))
                        );
                        
                        this.form.next(new Form("feature_prioritization", [
                            new FormGroup("Features File", FEATURE_PRIORITIZATION_FEATURES_FILE_HELP_CONTENT, [
                                new FileFormField("features_file", null, null, "Select \"omics\" features file", "Features File", true, null, this.fileService, this.jobService, false, false, VALID_UNLESS_REQUIRED_BUT_EMPTY, ALWAYS)
                            ]),
                            new FormGroup("Response File", FEATURE_PRIORITIZATION_RESPONSE_FILE_HELP_CONTENT, [
                                new FileFormField("response_file", null, null, "Select response file", "Response File", true, null, this.fileService, this.jobService, false, false, VALID_UNLESS_REQUIRED_BUT_EMPTY, ALWAYS)
                            ]),
                            new FormGroup("Network", FEATURE_PRIORITIZATION_NETWORK_HELP_CONTENT, networkFields),
                            new FormGroup("Parameters", FEATURE_PRIORITIZATION_PARAMETERS_HELP_CONTENT, [
                                new SelectFormField("correlation_method", null, "1", "Select the primary prioritization method", "Method", true, [
                                    new SelectOption("Absolute Pearson Correlation", "pearson", true),
                                    new SelectOption("T-test", "t_test", false),
                                    new SelectOption("EdgeR (for RNA-seq raw counts)", "edgeR", false)
                                    ], false, VALID_UNLESS_REQUIRED_BUT_EMPTY, IF('use_network', false)),
                                new SelectFormField("correlation_method", null, "1", "Select the primary prioritization method", "Method", true, [
                                    new SelectOption("Absolute Pearson Correlation", "pearson", true),
                                    new SelectOption("T-test", "t_test", false)
                                    ], false, VALID_UNLESS_REQUIRED_BUT_EMPTY, IF('use_network', true)),
                                new SelectFormField("missing_values_method", null, "2", "Select the method to handle missing \"omics\" values", "Missing Values", true, [
                                    new SelectOption("Average", "average", true),
                                    new SelectOption("Remove", "remove", false),
                                    new SelectOption("Reject", "reject", false)
                                    ], false, VALID_UNLESS_REQUIRED_BUT_EMPTY, ALWAYS),
                                // top N features for network and no-network cases
                                new NumberFormField("num_response_correlated_features", null, "3", "Number of response-correlated features", "# Response-Correlated Features", true, 100, NumberType.INTEGER, false, 1, null, SLIDER_NONE, VALID_NUMBER, IF('use_network', true)),
                                new NumberFormField("num_exported_features", null, "4", "Number of exported features per phenotype", "# Exported Features", true, 100, NumberType.INTEGER, false, 1, null, SLIDER_NONE, VALID_NUMBER, IF('use_network', true)),
                                new NumberFormField("num_exported_features", null, "3", "Number of exported features per phenotype", "# Exported Features", true, 100, NumberType.INTEGER, false, 1, null, SLIDER_NONE, VALID_NUMBER, IF('use_network', false)),
                                // other parameters
                                new NumberFormField("l1_regularization", null, "4", "L1 Regularization Coefficient", "L1 Regularization Coefficient", true, 0.1, NumberType.FLOAT, false, 0, null, SLIDER_NONE, VALID_NUMBER, OR([IF('correlation_method', 'elastic_net'), IF('correlation_method', 'lasso')])),
                                new BooleanFormField("fit_intercept", null, "5", "Fit Intercept", "Fit Intercept", true, true, VALID_UNLESS_REQUIRED_BUT_EMPTY, IF('correlation_method', 'lasso')),
                                new NumberFormField("l2_regularization", null, "5", "L2 Regularization Coefficient", "L2 Regularization Coefficient", true, 1, NumberType.FLOAT, false, 0, null, SLIDER_NONE, VALID_NUMBER, IF('correlation_method', 'elastic_net')),
                                new BooleanFormField("fit_intercept", null, "6", "Fit Intercept", "Fit Intercept", true, true, VALID_UNLESS_REQUIRED_BUT_EMPTY, IF('correlation_method', 'elastic_net')),
                            ]),
                            new FormGroup("Bootstrapping", FEATURE_PRIORITIZATION_BOOTSTRAPPING_HELP_CONTENT, [
                                new BooleanFormField("use_bootstrapping", "Do you want to use bootstrapping?", null, null, "Use Bootstrapping", true, null, VALID_UNLESS_REQUIRED_BUT_EMPTY, ALWAYS),
                                new NumberFormField("num_bootstraps", null, "1", "Enter the number of bootstraps to use in your analysis", "# Bootstraps", true, 8, NumberType.INTEGER, false, 1, 200, SLIDER_NONE, VALID_NUMBER, IF('use_bootstrapping', true)),
                                new NumberFormField("bootstrap_sample_percent", null, "2", "Enter the bootstrap sample percent", "Sample %", true, 80, NumberType.FLOAT, true, 0, 100, SLIDER_NO_LABELS, VALID_NUMBER, IF('use_bootstrapping', true)),
                                new HiddenFormField("method", "Robust-ProGENI", AND([IF('use_network', true), IF('use_bootstrapping', true)])),
                                new HiddenFormField("method", "ProGENI", AND([IF('use_network', true), IF('use_bootstrapping', false)])),
                                new HiddenFormField("method", "Robust Pearson Correlation", AND([IF('correlation_method', 'pearson'), IF('use_network', false), IF('use_bootstrapping', true)])),
                                new HiddenFormField("method", "Robust LASSO", AND([IF('correlation_method', 'lasso'), IF('use_network', false), IF('use_bootstrapping', true)])),
                                new HiddenFormField("method", "Robust EN", AND([IF('correlation_method', 'elastic_net'), IF('use_network', false), IF('use_bootstrapping', true)])),
                                new HiddenFormField("method", "Pearson Correlation", AND([IF('correlation_method', 'pearson'), IF('use_network', false), IF('use_bootstrapping', false)])),
                                new HiddenFormField("method", "LASSO", AND([IF('correlation_method', 'lasso'), IF('use_network', false), IF('use_bootstrapping', false)])),
                                new HiddenFormField("method", "EN", AND([IF('correlation_method', 'elastic_net'), IF('use_network', false), IF('use_bootstrapping', false)])),
                                new HiddenFormField("method", "T-Test", AND([IF('correlation_method', 't_test'), IF('use_network', false), IF('use_bootstrapping', false)])),
                                new HiddenFormField("method", "Robust T-Test", AND([IF('correlation_method', 't_test'), IF('use_network', false), IF('use_bootstrapping', true)])),
                                new HiddenFormField("cloud", "aws", ALWAYS)
                                
                            ])
                            //remove cloud hidden field, too
                            //]),
                            //new FormGroup("Cloud", SAMPLE_HELP_CONTENT, [
                            //    new SelectFormField("cloud", "Choose a cloud computing resource.", null, "Select a cloud computing resource on which to run your analysis", "Cloud", true, [
                            //        new SelectOption("Amazon", "aws", true, ALWAYS)
                            //        ], false, VALID_UNLESS_REQUIRED_BUT_EMPTY, ALWAYS)
                        ]));

                        joinedStreamSubscription.unsubscribe();
                    }
                );

                return this.form.asObservable();
            }
        );
    }
}

var FEATURE_PRIORITIZATION_ABOUT = "You have a spreadsheet of transcriptomic data on a collection of biological samples (or any other &ldquo;omics&rdquo; data set that assigns each feature a numeric value in each sample). You also have a continuous-valued (e.g., drug response in the form of IC50) or binary-valued (e.g., case vs. control) phenotype measurement for each sample. You want to find features most associated with the phenotype, or maybe you want to rank all features by their potential association with the phenotype. This pipeline scores each feature by the association between its &ldquo;omic&rdquo; value (e.g., expression) and the phenotype, and gives you the top phenotype-related features. If your features are genes, you also have the option of using the Knowledge Network in this pipeline, which allows you to incorporate prior information in the form of interaction among genes to capture indirect associations of genes with the phenotype.";

var FEATURE_PRIORITIZATION_TRAINING = new HelpContentGroup("Info and training", [
    new HelpContentElement("Quickstart Guide", HelpElementType.HEADING),
    new HelpContentElement("This guide walks you through the entire pipeline from setup to visualization of results. It also includes links to sample data.", HelpElementType.BODY),
    new HelpContentElement("<a href='https://knoweng.org/quick-start/' target='_blank'>Download the Feature Prioritization Quickstart Guide PDF</a>", HelpElementType.BODY),
    new HelpContentElement("Video Tutorials", HelpElementType.HEADING),
    new HelpContentElement("The KnowEnG YouTube Channel contains videos for every pipeline (some currently in development) as well as information about unique attributes of the KnowEnG Platform.", HelpElementType.BODY),
    new HelpContentElement("<a href='https://www.youtube.com/channel/UCjyIIolCaZIGtZC20XLBOyg' target='_blank'>Visit the KnowEnG YouTube Channel</a>", HelpElementType.BODY)
]);

var FEATURE_PRIORITIZATION_OVERVIEW_HELP_CONTENT = new HelpContent([
    new HelpContentGroup("About Feature Prioritization", [
        new HelpContentElement(FEATURE_PRIORITIZATION_ABOUT, HelpElementType.BODY)
    ]),
    new HelpContentGroup("How does this work?", [
        new HelpContentElement("This pipeline first tries to predict the phenotype of a sample from a feature's value (e.g., a gene's expression) in that sample. It can do this one feature at a time, or using multiple features together. Either way, it identifies a set of features associated with the phenotype. Next, if your features are genes, you can choose to give this feature set a &ldquo;Knowledge Network boost.&rdquo; In this optional step, the pipeline employs state-of-the-art data mining techniques similar to Google's search algorithm to identify additional genes that are highly related to the above set of phenotype-related genes.", HelpElementType.BODY)
    ]),
    new HelpContentGroup("How is this different?", [
        new HelpContentElement("The first step of identifying phenotype-related features is fairly standard, relying on popular statistical methods such as correlation coefficients, or multiple regression. The option of &ldquo;Knowledge Network boost&rdquo; is what makes this pipeline unique. If you choose this option, you can incorporate prior knowledge of gene-gene relationships, such as protein-protein interactions, genetic interactions, co-expression, etc., while identifying phenotype-related genes.", HelpElementType.BODY)
    ]),
    new HelpContentGroup("What do I provide?", [
        new HelpContentElement("A spreadsheet of &ldquo;omics&rdquo; data, with rows for features and columns for samples.", HelpElementType.BODY),
        new HelpContentElement("Also, a &ldquo;response file&rdquo; that includes the phenotype measurement on each sample.", HelpElementType.BODY)
    ]),
    new HelpContentGroup("What output does this produce?", [
        new HelpContentElement("A ranked list of features associated with phenotype.", HelpElementType.BODY)
    ]),
    FEATURE_PRIORITIZATION_TRAINING
]);

var FEATURE_PRIORITIZATION_FEATURES_FILE_HELP_CONTENT = new HelpContent([
    new HelpContentGroup("What is the &ldquo;&lsquo;omics&rsquo; features file&rdquo;?", [
        new HelpContentElement("This is the file with feature-level &ldquo;omics&rdquo; profiles of your collection of samples. A common example is transcriptomic data (e.g., from microarray or RNA-seq). Its rows represent features and columns are samples.", HelpElementType.BODY)
    ]),
    new HelpContentGroup("Data Preparation", [
        new HelpContentElement("In the analysis, we assume that the values for each feature follow a normal distribution. So to obtain the best results, we suggest you first apply appropriate transformations to your data (e.g. log2 transform to microarray data) to satisfy this condition.", HelpElementType.BODY)
    ]),
    new HelpContentGroup("Acceptable Data Formats", [
        new HelpContentElement("Currently, the input files must be tab delimited (e.g., tsv or txt formats).", HelpElementType.BODY)
    ]),
    FEATURE_PRIORITIZATION_TRAINING
]);

var FEATURE_PRIORITIZATION_RESPONSE_FILE_HELP_CONTENT = new HelpContent([
    new HelpContentGroup("What is the &ldquo;response file&rdquo;?", [
        new HelpContentElement("This is the file with phenotype values, one for each sample. The collection of samples must be the same as those in the omic data spreadsheet. Its rows represent samples and columns represent phenotype (or phenotypes) of interest.", HelpElementType.BODY)
    ]),
    new HelpContentGroup("Data Preparation", [
        new HelpContentElement("No specific transformation is necessary for the response data; however, if the phenotype corresponds to drug response IC50 or AUC, it is preferable that these values are in log scale. In addition, NAs are allowed in the response file.", HelpElementType.BODY)
    ]),
    new HelpContentGroup("Acceptable Data Formats", [
        new HelpContentElement("Currently, the input files must be tab delimited (e.g., tsv or txt formats).", HelpElementType.BODY)
    ]),
    FEATURE_PRIORITIZATION_TRAINING
]);

var FEATURE_PRIORITIZATION_PARAMETERS_HELP_CONTENT = new HelpContent([
    new HelpContentGroup("What is a &ldquo;primary prioritization method&rdquo;?", [
        new HelpContentElement("This is the statistical method that will be used to relate an omics feature's values to the phenotype.", HelpElementType.BODY),
        new HelpContentElement("Absolute Pearson Correlation", HelpElementType.HEADING),
        new HelpContentElement("Pearson correlation is a popular statistical technique to measure the linear dependence of two variables.", HelpElementType.BODY),
        new HelpContentElement("If your phenotype data is continuous-valued and properly normalized (e.g. drug response in the form of IC50) and your features' omics values are also continuous-valued and are properly normalized, use this test.", HelpElementType.BODY),
        new HelpContentElement("T-test", HelpElementType.HEADING),
        new HelpContentElement("T-test is a popular statistical test which is used to determine if two sets of data are significantly different from each other. This test assumes that the data follows a Normal distribution.", HelpElementType.BODY),
        new HelpContentElement("If your phenotype data is binary (e.g. case/control, or after/before treatment) and your features' omics values are properly normalized, use this test.", HelpElementType.BODY),
        new HelpContentElement("EdgeR", HelpElementType.HEADING),
        new HelpContentElement("EdgeR is a tool that provides statistical approaches for assessing differential expression from sequencing based experiments like RNA-seq. If your phenotype data is binary (e.g. case/control, or after/before treatment) and your features' omics values are the original raw read counts from a sequencing experiment, use this test. This option is only available if you are not using the Knowledge Network.", HelpElementType.BODY)
    ]),
    /*
    new HelpContentGroup("Method 2: LASSO", [
        new HelpContentElement("About", HelpElementType.HEADING),
        new HelpContentElement("Lasso is the name of a popular statistical technique, which as applied here can predict the numeric phenotype from the omic values of many features taken together. It is similar to Elastic Net, with some technical differences.", HelpElementType.BODY),
        new HelpContentElement("What is Regularization Coefficient?", HelpElementType.HEADING),
        new HelpContentElement("When Lasso attempts to predict the phenotype from omic values of thousands of features together, it encounters the problem of &ldquo;over-fitting.&rdquo; It will do a bad job at prediction unless it is forced to select a reasonably sized subset of features to use as predictors. The Regularization Coefficient is how you tell Lasso to select a small set of predictors. The larger this number the stronger is the pressure on Lasso to use only a few features.", HelpElementType.BODY),
        new HelpContentElement("Should I &ldquo;fit intercept&rdquo;?", HelpElementType.HEADING),
        new HelpContentElement("In most cases, fitting intercept is recommended.", HelpElementType.BODY)
    ]),
    */
    /*
    new HelpContentGroup("Method 3: ELASTIC NET", [
        new HelpContentElement("About", HelpElementType.HEADING),
        new HelpContentElement("Elastic Net is the name of a popular statistical technique, which as applied here can predict the numeric phenotype from the omic values of many features taken together. It is similar to Lasso, with some technical differences.", HelpElementType.BODY),
        new HelpContentElement("What are L1 and L2 Regularization Coefficients?", HelpElementType.HEADING),
        new HelpContentElement("When Elastic Net attempts to predict the phenotype from omic values of thousands of features together, it encounters the problem of &ldquo;over-fitting.&rdquo; It will do a bad job at prediction unless it is forced to select a reasonably sized subset of features to use as predictors. The Regularization Coefficients are how you tell Elastic Net to select a small set of predictors. The larger these numbers the stronger is the pressure on Elastic Net to use only a few features.", HelpElementType.BODY),
        new HelpContentElement("Should I &ldquo;fit intercept&rdquo;?", HelpElementType.HEADING),
        new HelpContentElement("In most cases, fitting intercept is recommended.", HelpElementType.BODY)
    ])*/
    new HelpContentGroup("What are the options for handling missing values?", [
        new HelpContentElement("Average", HelpElementType.HEADING),
        new HelpContentElement("For each feature, any samples that do not have a value for the feature will be assigned the average value of the feature.", HelpElementType.BODY),
        new HelpContentElement("Remove", HelpElementType.HEADING),
        new HelpContentElement("Any features with missing values will be excluded from the analysis.", HelpElementType.BODY),
        new HelpContentElement("Reject", HelpElementType.HEADING),
        new HelpContentElement("If any missing values are found in the &ldquo;omics&rdquo; spreadsheet, the analysis will fail with an error message identifying the presence of missing values.", HelpElementType.BODY)
    ]),
    new HelpContentGroup("How should I choose the number of response-correlated features?", [
        new HelpContentElement("If you are using the Knowledge Network, the response-correlated features are features that are used in the random walk with restarts algorithm of ProGENI as the restart set. Most often, this value is set between 0.5% and 5% of the number of features in the spreadsheet, and the results are typically stable within that range.", HelpElementType.BODY),
        new HelpContentElement("If you are not using the Knowledge Network, this option is not available.", HelpElementType.BODY)
    ]),
    new HelpContentGroup("What are exported features?", [
        new HelpContentElement("This pipeline produces summary tables of the top features per phenotype. These summary tables can be used as inputs to other pipelines or downloaded for use outside the KnowEnG platform. Here you can select how many top features to export per phenotype.", HelpElementType.BODY)
    ]),
    FEATURE_PRIORITIZATION_TRAINING
]);

var FEATURE_PRIORITIZATION_NETWORK_HELP_CONTENT = new HelpContent([
    new HelpContentGroup("What does it mean to use the Knowledge Network?", [
        new HelpContentElement("Briefly, if your features are genes, the network makes use of known relationships such as protein-protein interactions, genetic interactions and homology relationships among genes. Normally, when trying to relate genes to the phenotype, one considers each gene separately, or relies on statistical methods to identify combinations of genes that are together predictive of the phenotype. To incorporate large amounts of prior knowledge about gene-gene relationships with &ldquo;omic&rdquo; data in the prioritization task, we use the ProGENI algorithm (Prioritization of Genes Enhanced with Network Information) which combines the expression of the genes with the activity level of their neighbors in the network.  For example, a gene whose omic value is only moderately correlated with the phenotype may be known to be closely related (say by PPI or homology) to other genes that are highly predictive of the phenotype. In such a case, ProGENI selects that gene as relevant to the phenotype.", HelpElementType.BODY)
    ]),
    new HelpContentGroup("Advantages", [
        new HelpContentElement("We have shown that a significant improvement in prediction of drug response based on prioritized genes can be obtained if network information is incorporated with gene expression data using the ProGENI algorithm (implemented in this pipeline). In addition, we have shown that many genes identified using this algorithm have been experimentally (using siRNA knockdown and other methods) verified to affect the drug sensitivity in different cell lines. See the ProGENI paper (preprint doi: <a href='https://doi.org/10.1101/090027' target='_blank'>https://doi.org/10.1101/090027</a>) for more details.", HelpElementType.BODY)
    ]),
    new HelpContentGroup("Disadvantages", [
        new HelpContentElement("This is a novel approach to gene prioritization. It has been less widely used than the standard approach without the Knowledge Network.", HelpElementType.BODY)
    ]),
    new HelpContentGroup("What is an Interaction Network?", [
        new HelpContentElement("ProGENI utilizes prior knowledge about gene-gene relationships to improve the ranking genes associated with the phenotype. These relationships are represented as a network of genes, with each edge representing a relationship, such as protein-protein physical interaction, genetic interactions, co-expression, etc. Each such network is called an Interaction Network. You can choose which types of relationships to include in the interaction network.", HelpElementType.BODY)
    ]),
    new HelpContentGroup("Network Influence", [
        new HelpContentElement("ProGENI employs random walk with restarts to incorporate network information. Network influence is the algorithm's probability that controls whether the walker's next move is to follow a network edge versus to jump back to a node from the query gene set (also known as the set of response correlated genes). Most often, the network influence is set to a value between 40% and 60% and the results are typically stable within that range.", HelpElementType.BODY),
        new HelpContentElement("0% - No Network Influence (equivalent to the absolute Pearson correlation method)", HelpElementType.BODY),
        new HelpContentElement("100% - Network Only (the effect of phenotype is ignored)", HelpElementType.BODY)
    ]),
    FEATURE_PRIORITIZATION_TRAINING
]);

var FEATURE_PRIORITIZATION_BOOTSTRAPPING_HELP_CONTENT = new HelpContent([
    new HelpContentGroup("What is bootstrapping?", [
        new HelpContentElement("Bootstrapping or bootstrap sampling refers to randomly selecting (with replacement) subsets of samples to use in the prioritization method. Each subset of samples is used to obtain a ranked list of features, and these ranked lists are aggregated to obtain a final ranking which is robust to noise in the data. We use Borda scores to aggregate these lists.", HelpElementType.BODY)
    ]),
    new HelpContentGroup("How should I choose the number of bootstraps?", [
        new HelpContentElement("Bootstrap sampling is used to obtain a more robust ranking, and more bootstraps can obtain more robust results. However, a large value will increase the computational cost and the amount of time it takes for the results to be ready.", HelpElementType.BODY)
    ]),
    new HelpContentGroup("How should I choose the bootstrap sample percentage?", [
        new HelpContentElement("If number of bootstraps is larger than 1, you should choose a percentage less than 100. Most often, sample percentage is set to a value between 60% and 90%.", HelpElementType.BODY)
    ]),
    FEATURE_PRIORITIZATION_TRAINING
]);
