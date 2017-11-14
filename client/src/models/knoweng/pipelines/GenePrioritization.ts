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

export class GenePrioritizationPipeline extends Pipeline {
    
    private form = new Subject<Form>();

    constructor(
        private fileService: FileService,
        speciesStream: Observable<Species[]>,
        networksStream: Observable<AnalysisNetwork[]>) {
            
        super(
            "Gene Prioritization",
            "gene_prioritization",
            GENE_PRIORITIZATION_ABOUT,
            GENE_PRIORITIZATION_OVERVIEW_HELP_CONTENT,
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
                            new FileFormField("features_file", null, "2", "Select genomic features file", "Features File", true, null, this.fileService, false, false, VALID_UNLESS_REQUIRED_BUT_EMPTY, ALWAYS)
                        ]);
                        
                        networkFields.push(
                            new BooleanFormField("use_network", "Do you want to use the Knowledge Network?", null, null, "Use Network", true, null, VALID_UNLESS_REQUIRED_BUT_EMPTY, ALWAYS)
                        );
                        getInteractionNetworkOptions(species, networks).forEach(nf => {
                            networkFields.push(nf);
                        });
                        networkFields.push(
                            new NumberFormField("network_influence", null, "2", "Choose amount of network influence", "Network Influence", true, 50, NumberType.FLOAT, true, 0, 100, new NumberFormFieldSlider("data driven", "network driven"), VALID_NUMBER, IF('use_network', true))
                        );
                        networkFields.push(
                            new NumberFormField("num_response_correlated_genes", null, "3", "Number of response-correlated genes", "# Response-Correlated Genes", true, 100, NumberType.INTEGER, false, 1, null, SLIDER_NONE, VALID_NUMBER, IF('use_network', true))
                        );
                        
                        this.form.next(new Form("gene_prioritization", [
                            new FormGroup("Features File", GENE_PRIORITIZATION_FEATURES_FILE_HELP_CONTENT, featuresFileFields),
                            new FormGroup("Response File", GENE_PRIORITIZATION_RESPONSE_FILE_HELP_CONTENT, [
                                new FileFormField("response_file", null, null, "Select response file", "Response File", true, null, this.fileService, false, false, VALID_UNLESS_REQUIRED_BUT_EMPTY, ALWAYS)
                            ]),
                            new FormGroup("Parameters", GENE_PRIORITIZATION_PARAMETERS_HELP_CONTENT, [
                                new SelectFormField("correlation_method", null, "1", "Select the primary prioritization method", "Method", true, [
                                    new SelectOption("Absolute Pearson Correlation", "pearson", true),
                                    new SelectOption("T-test", "t_test", false)
                                    ], false, VALID_UNLESS_REQUIRED_BUT_EMPTY, ALWAYS),
                                new NumberFormField("l1_regularization", null, "2", "L1 Regularization Coefficient", "L1 Regularization Coefficient", true, 0.1, NumberType.FLOAT, false, 0, null, SLIDER_NONE, VALID_NUMBER, OR([IF('correlation_method', 'elastic_net'), IF('correlation_method', 'lasso')])),
                                new BooleanFormField("fit_intercept", null, "3", "Fit Intercept", "Fit Intercept", true, true, VALID_UNLESS_REQUIRED_BUT_EMPTY, IF('correlation_method', 'lasso')),
                                new NumberFormField("l2_regularization", null, "3", "L2 Regularization Coefficient", "L2 Regularization Coefficient", true, 1, NumberType.FLOAT, false, 0, null, SLIDER_NONE, VALID_NUMBER, IF('correlation_method', 'elastic_net')),
                                new BooleanFormField("fit_intercept", null, "4", "Fit Intercept", "Fit Intercept", true, true, VALID_UNLESS_REQUIRED_BUT_EMPTY, IF('correlation_method', 'elastic_net')),
                            ]),
                            new FormGroup("Network", GENE_PRIORITIZATION_NETWORK_HELP_CONTENT, networkFields),
                            new FormGroup("Bootstrapping", GENE_PRIORITIZATION_BOOTSTRAPPING_HELP_CONTENT, [
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

var GENE_PRIORITIZATION_ABOUT = "You have a spreadsheet of transcriptomic data on a collection of biological samples (or any other &ldquo;omics&rdquo; data set that assigns each gene a numeric value in each sample). You also have a continuous-valued (e.g., drug response in the form of IC50) or binary-valued phenotype (e.g., case vs. control) measurement for each sample. You want to find genes most associated with the phenotype, or maybe you want to rank all genes by their potential association with the phenotype. This pipeline scores each gene by the association between its &ldquo;omic&rdquo; value (e.g., expression) and the phenotype, and gives you the top phenotype-related genes. You also have the option of using the Knowledge Network in this pipeline, which allows you to incorporate prior information in the form of interaction among genes to capture indirect associations of genes with the phenotype.";

var GENE_PRIORITIZATION_TRAINING = new HelpContentGroup("Info and training", [
    new HelpContentElement("Quickstart Guide", HelpElementType.HEADING),
    new HelpContentElement("This guide walks you through the entire pipeline from setup to visualization of results. It also includes links to sample data.", HelpElementType.BODY),
    new HelpContentElement("<a href='//www.knoweng.org/quick-start/' target='_blank'>Download the Gene Prioritization Quickstart Guide PDF</a>", HelpElementType.BODY),
    new HelpContentElement("Video Tutorials", HelpElementType.HEADING),
    new HelpContentElement("The KnowEnG YouTube Channel contains videos for every pipeline (some currently in development) as well as information about unique attributes of the KnowEnG Platform.", HelpElementType.BODY),
    new HelpContentElement("<a href='//www.youtube.com/channel/UCjyIIolCaZIGtZC20XLBOyg' target='_blank'>Visit the KnowEnG YouTube Channel</a>", HelpElementType.BODY)
]);

var GENE_PRIORITIZATION_OVERVIEW_HELP_CONTENT = new HelpContent([
    new HelpContentGroup("About Gene Prioritization", [
        new HelpContentElement(GENE_PRIORITIZATION_ABOUT, HelpElementType.BODY)
    ]),
    new HelpContentGroup("How does this work?", [
        new HelpContentElement("This pipeline first tries to predict the numeric phenotype of a sample from a gene's expression (or other &ldquo;omic&rdquo;) value in that sample. It can do this one gene at a time, or using multiple genes together. Either way, it identifies a set of genes associated with the phenotype. Next, you can choose to give this gene set a &ldquo;Knowledge Network boost.&rdquo; In this optional step, the pipeline employs state-of-the-art data mining techniques similar to Google's search algorithm to identify additional genes that are highly related to the above set of phenotype-related genes.", HelpElementType.BODY)
    ]),
    new HelpContentGroup("How is this different?", [
        new HelpContentElement("The first step of identifying phenotype-related genes is fairly standard, relying on popular statistical methods such as correlation coefficients, or multiple regression. The option of &ldquo;Knowledge Network boost&rdquo; is what makes this pipeline unique. If you choose this option, you can incorporate prior knowledge of gene-gene relationships, such as protein-protein interactions, genetic interactions, co-expression, etc., while identifying phenotype-related genes.", HelpElementType.BODY)
    ]),
    new HelpContentGroup("What do I provide?", [
        new HelpContentElement("A spreadsheet of transcriptomic data, with rows for genes and columns for samples. In place of transcriptomic data, any other &ldquo;omic&rdquo; data that assigns a numeric measurement to each gene (row) in each sample (column) will work.", HelpElementType.BODY),
        new HelpContentElement("Also, a &ldquo;response file&rdquo; that includes the phenotype measurement on each sample.", HelpElementType.BODY)
    ]),
    new HelpContentGroup("What output does this produce?", [
        new HelpContentElement("A ranked list of genes associated with phenotype.", HelpElementType.BODY)
    ]),
    GENE_PRIORITIZATION_TRAINING
]);

var GENE_PRIORITIZATION_FEATURES_FILE_HELP_CONTENT = new HelpContent([
    new HelpContentGroup("What is the &ldquo;omic&rdquo; data spreadsheet?", [
        new HelpContentElement("This is the file with gene-level omics profiles of your collection of samples. A common example is transcriptomic data (e.g., from microarray or RNA-seq). Its rows represent genes and columns are samples.", HelpElementType.BODY)
    ]),
    new HelpContentGroup("Data Preparation", [
        new HelpContentElement("In the analysis, we assume that the transcriptomic data for each gene follows a normal distribution. So to obtain the best results, we suggest you first apply appropriate transformations to your data (e.g. log2 transform to microarray data) to satisfy this condition. In addition, at this point we require the transcriptomic spreadsheet not to contain any NA values.", HelpElementType.BODY)
    ]),
    new HelpContentGroup("Acceptable Data Formats", [
        new HelpContentElement("Currently, the input files must be tab delimited (e.g., tsv or txt formats).", HelpElementType.BODY)
    ]),
    GENE_PRIORITIZATION_TRAINING
]);

var GENE_PRIORITIZATION_RESPONSE_FILE_HELP_CONTENT = new HelpContent([
    new HelpContentGroup("What is the &ldquo;response file&rdquo;?", [
        new HelpContentElement("This is the file with phenotype values, one for each sample. The collection of samples must be the same as those in the omic data spreadsheet. Its rows represent samples and columns represent phenotype (or phenotypes) of interest.", HelpElementType.BODY)
    ]),
    new HelpContentGroup("Data Preparation", [
        new HelpContentElement("No specific transformation is necessary for the response data; however, if the phenotype corresponds to drug response IC50 or AUC, it is preferable that these values are in log scale. In addition, NAs are allowed in the response file.", HelpElementType.BODY)
    ]),
    new HelpContentGroup("Acceptable Data Formats", [
        new HelpContentElement("Currently, the input files must be tab delimited (e.g., tsv or txt formats).", HelpElementType.BODY)
    ]),
    GENE_PRIORITIZATION_TRAINING
]);

var GENE_PRIORITIZATION_PARAMETERS_HELP_CONTENT = new HelpContent([
    new HelpContentGroup("What is a &ldquo;primary prioritization method&rdquo;?", [
        new HelpContentElement("This is the statistical method that will be used to relate a gene's omics value to the phenotype. If you do not want to use the network, this statistical test will be used to rank genes. If you want to use the network, this statistical test will be utilized as part of the pipeline to rank genes.", HelpElementType.BODY)
    ]),
    new HelpContentGroup("Method 1: ABSOLUTE PEARSON CORRELATION", [
        new HelpContentElement("About", HelpElementType.HEADING),
        new HelpContentElement("Pearson correlation is a popular statistical technique to measure the linear dependence of two variables.", HelpElementType.BODY),
        new HelpContentElement("When should I use Pearson correlation?", HelpElementType.HEADING),
        new HelpContentElement("If your phenotype data is continuous-valued and properly normalized (e.g. drug response in the form of IC50) and your genes' omics values are also continuous-valued and are properly normalized, use this test.", HelpElementType.BODY)
    ]),
    new HelpContentGroup("Method 2: T-TEST", [
        new HelpContentElement("About", HelpElementType.HEADING),
        new HelpContentElement("T-test is a popular statistical test which is used to determine if two sets of data are significantly different from each other. This test assumes that the data follows a Normal distribution.", HelpElementType.BODY),
        new HelpContentElement("When should I use T-test?", HelpElementType.HEADING),
        new HelpContentElement("If your phenotype data is binary (e.g. case/control, or after/before treatment) and your genes' omics values are properly normalized, use this test.", HelpElementType.BODY)
    ]),
    /*
    new HelpContentGroup("Method 2: LASSO", [
        new HelpContentElement("About", HelpElementType.HEADING),
        new HelpContentElement("Lasso is the name of a popular statistical technique, which as applied here can predict the numeric phenotype from the omic values of many genes taken together. It is similar to Elastic Net, with some technical differences.", HelpElementType.BODY),
        new HelpContentElement("What is Regularization Coefficient?", HelpElementType.HEADING),
        new HelpContentElement("When Lasso attempts to predict the phenotype from omic values of thousands of genes together, it encounters the problem of &ldquo;over-fitting.&rdquo; It will do a bad job at prediction unless it is forced to select a reasonably sized subset of genes to use as predictors. The Regularization Coefficient is how you tell Lasso to select a small set of predictors. The larger this number the stronger is the pressure on Lasso to use only a few genes.", HelpElementType.BODY),
        new HelpContentElement("Should I &ldquo;fit intercept&rdquo;?", HelpElementType.HEADING),
        new HelpContentElement("In most cases, fitting intercept is recommended.", HelpElementType.BODY)
    ]),
    */
    /*
    new HelpContentGroup("Method 3: ELASTIC NET", [
        new HelpContentElement("About", HelpElementType.HEADING),
        new HelpContentElement("Elastic Net is the name of a popular statistical technique, which as applied here can predict the numeric phenotype from the omic values of many genes taken together. It is similar to Lasso, with some technical differences.", HelpElementType.BODY),
        new HelpContentElement("What are L1 and L2 Regularization Coefficients?", HelpElementType.HEADING),
        new HelpContentElement("When Elastic Net attempts to predict the phenotype from omic values of thousands of genes together, it encounters the problem of &ldquo;over-fitting.&rdquo; It will do a bad job at prediction unless it is forced to select a reasonably sized subset of genes to use as predictors. The Regularization Coefficients are how you tell Elastic Net to select a small set of predictors. The larger these numbers the stronger is the pressure on Elastic Net to use only a few genes.", HelpElementType.BODY),
        new HelpContentElement("Should I &ldquo;fit intercept&rdquo;?", HelpElementType.HEADING),
        new HelpContentElement("In most cases, fitting intercept is recommended.", HelpElementType.BODY)
    ])*/
    GENE_PRIORITIZATION_TRAINING
]);

var GENE_PRIORITIZATION_NETWORK_HELP_CONTENT = new HelpContent([
    new HelpContentGroup("What does it mean to use the Knowledge Network?", [
        new HelpContentElement("Briefly, the network makes use of known relationships such as protein-protein interactions, genetic interactions and homology relationships among genes. Normally, when trying to relate genes to the phenotype, one considers each gene separately, or rely on statistical methods to identify combinations of genes that are together predictive of the phenotype. To incorporate large amounts of prior knowledge about gene-gene relationships with &ldquo;omic&rdquo; data in the prioritization task, we use the ProGENI algorithm (Prioritization of Genes Enhanced with Network Information) which combines the expression of the genes with the activity level of their neighbors in the network.  For example, a gene whose omic value is only moderately correlated with the phenotype may be known to be closely related (say by PPI or homology) to other genes that are highly predictive of the phenotype. In such a case, ProGENI selects that gene as relevant to the phenotype.", HelpElementType.BODY)
    ]),
    new HelpContentGroup("Advantages", [
        new HelpContentElement("We have shown that a significant improvement in prediction of drug response based on prioritized genes can be obtained if network information is incorporated with gene expression data using the ProGENI algorithm (implemented in this pipeline). In addition, we have shown that many genes identified using this algorithm have been experimentally (using siRNA knockdown and other methods) verified to affect the drug sensitivity in different cell lines. See the ProGENI paper (preprint doi: <a href='//doi.org/10.1101/090027' target='_blank'>https://doi.org/10.1101/090027</a>) for more details.", HelpElementType.BODY)
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
    new HelpContentGroup("How should I choose the number of response-correlated genes?", [
        new HelpContentElement("The response-correlated genes are genes which are used in the random walk with restarts algorithm of ProGENI as the restart set. Most often, this value is set between 0.5% and 5% of the genes in the spreadsheet, and the results are typically stable within that range.", HelpElementType.BODY)
    ]),
    GENE_PRIORITIZATION_TRAINING
]);

var GENE_PRIORITIZATION_BOOTSTRAPPING_HELP_CONTENT = new HelpContent([
    new HelpContentGroup("What is bootstrapping?", [
        new HelpContentElement("Bootstrapping or bootstrap sampling refers to randomly selecting (with replacement) subsets of samples to use in the prioritization method. Each subset of samples is used to obtain a ranked list of genes and these ranked lists are aggregated together to obtain a final ranking which is robust to noise in the data. We use Borda scores to aggregate these lists.", HelpElementType.BODY)
    ]),
    new HelpContentGroup("How should I choose the number of bootstraps?", [
        new HelpContentElement("Bootstrap sampling is used to obtain a more robust ranking, and more bootstraps can obtain more robust results. However, a large value will increase the computational cost and the amount of time it takes for the results to be ready.", HelpElementType.BODY)
    ]),
    new HelpContentGroup("How should I choose the bootstrap sample percentage?", [
        new HelpContentElement("If number of bootstraps is larger than 1, you should choose a percentage less than 100. Most often, sample percentage is set to a value between 60% and 90%.", HelpElementType.BODY)
    ]),
    GENE_PRIORITIZATION_TRAINING
]);
