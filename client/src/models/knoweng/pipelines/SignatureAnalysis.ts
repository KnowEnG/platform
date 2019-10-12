import {Observable} from 'rxjs/Observable';

import {HelpContent, HelpContentGroup, HelpContentElement, HelpElementType} from '../HelpContent';
import {Form, FormGroup, SelectFormField, SelectOption, FileFormField, HiddenFormField,
    VALID_UNLESS_REQUIRED_BUT_EMPTY, ALWAYS} from '../Form';
import {Pipeline} from '../Pipeline';
import {FileService} from '../../../services/knoweng/FileService';
import {JobService} from '../../../services/knoweng/JobService';

export class SignatureAnalysisPipeline extends Pipeline {
    
    constructor(
        private fileService: FileService,
        private jobService: JobService) {
            
        super(
            "Signature Analysis",
            "signature_analysis",
            SIGNATURE_ANALYSIS_ABOUT,
            SIGNATURE_ANALYSIS_OVERVIEW_HELP_CONTENT,
            () => {
                let form = new Form("signature_analysis", [
                    new FormGroup("Query File", SIGNATURE_ANALYSIS_FEATURES_FILE_HELP_CONTENT, [
                        new FileFormField("query_file", null, null, "Select \"omics\" query file", "Query File", true, null, this.fileService, this.jobService, false, false, VALID_UNLESS_REQUIRED_BUT_EMPTY, ALWAYS)
                    ]),
                    new FormGroup("Signatures File", SIGNATURE_ANALYSIS_SIGNATURES_FILE_HELP_CONTENT, [
                        new FileFormField("signatures_file", null, null, "Select signatures file", "Signatures File", true, null, this.fileService, this.jobService, false, false, VALID_UNLESS_REQUIRED_BUT_EMPTY, ALWAYS)
                    ]),
                    new FormGroup("Parameters", SIGNATURE_ANALYSIS_PARAMETERS_HELP_CONTENT, [
                        new SelectFormField("similarity_measure", null, "1", "Select the similarity measure", "Similarity Measure", true, [
                            new SelectOption("Cosine", "cosine", false),
                            new SelectOption("Pearson", "pearson", false),
                            new SelectOption("Spearman", "spearman", true)
                            ], false, VALID_UNLESS_REQUIRED_BUT_EMPTY, ALWAYS),
                        new HiddenFormField("cloud", "aws", ALWAYS)
                    ])
                    //remove cloud hidden field, too
                    //]),
                    //new FormGroup("Cloud", SAMPLE_HELP_CONTENT, [
                    //    new SelectFormField("cloud", "Choose a cloud computing resource.", null, "Select a cloud computing resource on which to run your analysis", "Cloud", true, [
                    //        new SelectOption("Amazon", "aws", true, ALWAYS)
                    //        ], false, VALID_UNLESS_REQUIRED_BUT_EMPTY, ALWAYS)
                ]);
            return Observable.of(form);
        });
    }
}

var SIGNATURE_ANALYSIS_ABOUT = "You have a &ldquo;query file&rdquo; of genomic profiles on a collection of biological samples. " + 
    "You also have a &ldquo;signatures file&rdquo; of library &ldquo;omics&rdquo; signatures determined in previous studies. You want to determine how strongly " +
    "each of the samples in your query file matches each of the library signatures in the signatures file.";

var SIGNATURE_ANALYSIS_TRAINING = new HelpContentGroup("Info and training", [
    new HelpContentElement("Quickstart Guide", HelpElementType.HEADING),
    new HelpContentElement("This guide walks you through the entire pipeline from setup to visualization of results. It also includes links to sample data.", HelpElementType.BODY),
    new HelpContentElement("<a href='https://knoweng.org/quick-start/' target='_blank'>Download the Signature Analysis Quickstart Guide PDF</a>", HelpElementType.BODY),
    new HelpContentElement("Video Tutorials", HelpElementType.HEADING),
    new HelpContentElement("The KnowEnG YouTube Channel contains videos for every pipeline (some currently in development) as well as information about unique attributes of the KnowEnG Platform.", HelpElementType.BODY),
    new HelpContentElement("<a href='https://www.youtube.com/channel/UCjyIIolCaZIGtZC20XLBOyg' target='_blank'>Visit the KnowEnG YouTube Channel</a>", HelpElementType.BODY)
]);

var SIGNATURE_ANALYSIS_OVERVIEW_HELP_CONTENT = new HelpContent([
    new HelpContentGroup("About Signature Analysis", [
        new HelpContentElement(SIGNATURE_ANALYSIS_ABOUT, HelpElementType.BODY)
    ]),
    new HelpContentGroup("How does this work?", [
        new HelpContentElement("This pipeline will find the list of common &ldquo;omics&rdquo; features between the query file and the signatures file. " + 
            "It will then rank the library signatures in order of the selected similarity measure for each query sample.", HelpElementType.BODY)
    ]),
    new HelpContentGroup("What do I provide?", [
        new HelpContentElement("A &ldquo;query file,&rdquo;, with rows for &ldquo;omics&rdquo; features and columns for samples.", HelpElementType.BODY),
        new HelpContentElement("Also, a &ldquo;signatures file&rdquo; that includes the library signatures, with rows for &ldquo;omics&rdquo; features and columns for signatures.", HelpElementType.BODY)
    ]),
    new HelpContentGroup("What output does this produce?", [
        new HelpContentElement("A matrix of scores capturing the similarity between each sample and each signature.", HelpElementType.BODY)
    ]),
    SIGNATURE_ANALYSIS_TRAINING
]);

var SIGNATURE_ANALYSIS_FEATURES_FILE_HELP_CONTENT = new HelpContent([
    new HelpContentGroup("What is the &ldquo;query file&rdquo;?", [
        new HelpContentElement("This is the file with feature-level &ldquo;omics&rdquo; profiles of your collection of samples. A common example is transcriptomic data " + 
            "(e.g., from microarray or RNA-seq). Its rows represent features and columns are samples. The &ldquo;omics&rdquo; data in this file should be similar to that " + 
            "in the &ldquo;signatures file,&rdquo; in that the feature names should substantially overlap and the values should come from analogous measurements.", HelpElementType.BODY)
    ]),
    new HelpContentGroup("Data Preparation", [
        new HelpContentElement("No specific transformation is necessary for the query data.", HelpElementType.BODY)
    ]),
    new HelpContentGroup("Acceptable Data Formats", [
        new HelpContentElement("Currently, the input files must be tab delimited (e.g., tsv or txt formats).", HelpElementType.BODY)
    ]),
    SIGNATURE_ANALYSIS_TRAINING
]);

var SIGNATURE_ANALYSIS_SIGNATURES_FILE_HELP_CONTENT = new HelpContent([
    new HelpContentGroup("What is the &ldquo;signatures file&rdquo;?", [
        new HelpContentElement("This is the file with the &ldquo;omics&rdquo; signatures library data. Its rows correspond to &ldquo;omics&rdquo; features, and its columns correspond to the " + 
            "different signatures. The &ldquo;omics&rdquo; data in this file should be similar to that in the &ldquo;query file,&rdquo; in that the feature names should substantially " + 
            "overlap and the values should come from analogous measurements.", HelpElementType.BODY)
    ]),
    new HelpContentGroup("Data Preparation", [
        new HelpContentElement("No specific transformation is necessary for the signature data.", HelpElementType.BODY)
    ]),
    new HelpContentGroup("Acceptable Data Formats", [
        new HelpContentElement("Currently, the input files must be tab delimited (e.g., tsv or txt formats).", HelpElementType.BODY)
    ]),
    SIGNATURE_ANALYSIS_TRAINING
]);

var SIGNATURE_ANALYSIS_PARAMETERS_HELP_CONTENT = new HelpContent([
    new HelpContentGroup("What is a &ldquo;similarity measure&rdquo;?", [
        new HelpContentElement("This is the mathematical measure that will be used to compute the similarity between samples and library signatures. " +
            "The best choice will depend upon your data and your objective. Useful benchmarks and discussion can be found in " +
            "<a href='https://doi.org/10.1371/journal.pone.0068664'>Comparison of Profile Similarity Measures for Genetic Interaction Networks</a>.", HelpElementType.BODY),
    ]),
    SIGNATURE_ANALYSIS_TRAINING
]);
