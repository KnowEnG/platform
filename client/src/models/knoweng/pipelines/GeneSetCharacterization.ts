import 'rxjs/add/observable/forkJoin';
import {Observable} from 'rxjs/Observable';
import {Subject} from 'rxjs/Subject';
import {Subscription} from 'rxjs/Subscription';

import {HelpContent, HelpContentGroup, HelpContentElement, HelpElementType} from '../HelpContent';
import {Form, FormGroup, FormField, BooleanFormField, HiddenFormField, SelectFormField, SelectOption, FileFormField,
    NumberFormField, NumberType, NumberFormFieldSlider, VALID_UNLESS_REQUIRED_BUT_EMPTY, VALID_NUMBER, ALWAYS, IF} from '../Form';
import {Pipeline} from '../Pipeline';
import {getInteractionNetworkOptions} from './PipelineUtils';
import {AnalysisNetwork, Collection, Species} from '../KnowledgeNetwork';
import {FileService} from '../../../services/knoweng/FileService';
import {JobService} from '../../../services/knoweng/JobService';

export class GeneSetCharacterizationPipeline extends Pipeline {
    
    private form = new Subject<Form>();

    constructor(
        private fileService: FileService,
        private jobService: JobService,
        speciesStream: Observable<Species[]>,
        collectionsStream: Observable<Collection[]>,
        networksStream: Observable<AnalysisNetwork[]>) {

        super(
            "Gene Set Characterization",
            "gene_set_characterization",
            GENE_SET_CHARACTERIZATION_ABOUT,
            GENE_SET_CHARACTERIZATION_OVERVIEW_HELP_CONTENT,
            () => {
                // initialize kn-dependent data to empty arrays
                let speciesOptions: SelectOption[] = [];
                let collectionFields: FormField[] = [];
                let networkFields: FormField[] = [];
                let dataFields: FormField[] = [];

                // create subscription to populate arrays
                let joinedStream: Observable<any[]> = Observable.forkJoin(
                    speciesStream, collectionsStream, networksStream);
                let joinedStreamSubscription = joinedStream.subscribe(
                    (joinedArray: any[]) => {
                        // unpack data: first array will be species, second will be collections, third will be networks
                        let species: Species[] = joinedArray[0];
                        let collections: Collection[] = joinedArray[1];
                        let networks: AnalysisNetwork[] = joinedArray[2];

                        // populate arrays
                        speciesOptions = species.sort((a, b) => d3.ascending(a.display_order, b.display_order)).map(s => new SelectOption(s.name + " (" + s.short_latin_name + ")", s.species_number, s.selected_by_default, s.group_name));
                        Array.prototype.push.apply(dataFields, [
                            new SelectFormField("species", null, "1", "Select species", "Species", true, speciesOptions, false, VALID_UNLESS_REQUIRED_BUT_EMPTY, ALWAYS),
                            new FileFormField("gene_set_file", null, "2", "Select gene-identifiers list or spreadsheet", "Gene Set File", true, null, this.fileService, this.jobService, false, true, VALID_UNLESS_REQUIRED_BUT_EMPTY, ALWAYS)
                        ]);

                        // create a gene collections field for each species; they'll be enabled according to the current species selection, so only one will be visible at any given time
                        species.forEach(s => {
                            collectionFields.push(new SelectFormField("gene_collections", null, "1", "Choose public gene sets for comparison", "Collections to Compare", true,
                                collections.filter(c => c.species_number === s.species_number).map(c => new SelectOption(c.collection, c.edge_type_name, c.collection_selected_by_default, c.super_collection)),
                                true, VALID_UNLESS_REQUIRED_BUT_EMPTY, IF('species', s.species_number)));
                        });
                        // create a network name field for each species; they'll be enabled according to the current species selection, so only one will be visible at any given time
                        networkFields.push(
                            new BooleanFormField("use_network", "Do you want to use the Knowledge Network?", null, null, "Use Network", true, null, VALID_UNLESS_REQUIRED_BUT_EMPTY, ALWAYS)
                        );
                        networkFields.push(new HiddenFormField("method", "Fisher", IF('use_network', false)));
                        networkFields.push(new HiddenFormField("method", "DRaWR", IF('use_network', true)));
                        getInteractionNetworkOptions(species, networks, "1").forEach(nf => {
                            networkFields.push(nf);
                        });
                        networkFields.push(
                            new NumberFormField("network_smoothing", null, "2", "Choose the amount of network smoothing", "Network Smoothing", true, 50, NumberType.FLOAT, true, 0, 100, new NumberFormFieldSlider("data driven", "network driven"), VALID_NUMBER, IF('use_network', true))
                        );
                        networkFields.push(new HiddenFormField("cloud", "aws", ALWAYS));

                        this.form.next(new Form("gene_set_characterization", [
                            new FormGroup("Data", GENE_SET_CHARACTERIZATION_DATA_HELP_CONTENT, dataFields),
                            new FormGroup("Parameters", GENE_SET_CHARACTERIZATION_PARAMETERS_HELP_CONTENT, collectionFields),
                            new FormGroup("Network", GENE_SET_CHARACTERIZATION_NETWORK_HELP_CONTENT, networkFields)
                            //if enabling the section below, remove cloud hidden field that's currently part of networkFields
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

var GENE_SET_CHARACTERIZATION_ABOUT = "You have a set of genes. You want to know if these genes are enriched for a pathway, a Gene Ontology term, or other types of annotations. This pipeline tests your gene set for enrichment against a large compendium of annotations. You have the option of using a standard statistical test or a Knowledge Network-based approach similar to Google's PageRank algorithm.";

var GENE_SET_CHARACTERIZATION_TRAINING = new HelpContentGroup("Info and training", [
    new HelpContentElement("Quickstart Guide", HelpElementType.HEADING),
    new HelpContentElement("This guide walks you through the entire pipeline from setup to visualization of results. It also includes links to sample data.", HelpElementType.BODY),
    new HelpContentElement("<a href='https://knoweng.org/quick-start/' target='_blank'>Download the Gene Set Characterization Quickstart Guide PDF</a>", HelpElementType.BODY),
    new HelpContentElement("Video Tutorials", HelpElementType.HEADING),
    new HelpContentElement("The KnowEnG YouTube Channel contains videos for every pipeline (some currently in development) as well as information about unique attributes of the KnowEnG Platform.", HelpElementType.BODY),
    new HelpContentElement("<a href='https://www.youtube.com/channel/UCjyIIolCaZIGtZC20XLBOyg' target='_blank'>Visit the KnowEnG YouTube Channel</a>", HelpElementType.BODY)
]);

var GENE_SET_CHARACTERIZATION_OVERVIEW_HELP_CONTENT = new HelpContent([
    new HelpContentGroup("About Gene Set Characterization", [
        new HelpContentElement(GENE_SET_CHARACTERIZATION_ABOUT, HelpElementType.BODY),
    ]),
    new HelpContentGroup("How does the KnowEnG pipeline work?", [
        new HelpContentElement("This pipeline allows you to use a standard statistical test, called the Fisher's exact test, to assess the overlap between your submitted gene set(s) and pre-defined gene sets. This approach is commonly used for gene set characterization, for example by the popular <a href='https://david.ncifcrf.gov' target='_blank'>DAVID</a> tool.", HelpElementType.BODY),
        new HelpContentElement("Alternatively, you may choose a knowledge-guided method developed by us: DRaWR. This method employs state-of-the-art data mining techniques similar to Google's search algorithm to identify annotations&mdash;pathways, GO terms etc.&mdash;associated with many of your genes.", HelpElementType.BODY),
    ]),
    new HelpContentGroup("How is the KnowEnG pipeline different?", [
        new HelpContentElement("The Fisher's exact test that is widely used has been implemented in this pipeline.  The DRaWR option is different: It not only examines how many of your genes share an annotation, it also integrates cases where a gene in your set is known to be closely related, for example by homology, to a gene that shares the annotation. The method generalizes what it means for a gene set to be enriched for an annotation.", HelpElementType.BODY),
    ]),
    new HelpContentGroup("Pipeline inputs and outputs", [
        new HelpContentElement("The users supplies the gene identifiers of their gene set(s) in the form of a list or spreadsheet.", HelpElementType.BODY),
        new HelpContentElement("The pipeline outputs a ranked list of annotations (pathways, GO terms etc.) associated with the gene set.", HelpElementType.BODY),
    ]),
    GENE_SET_CHARACTERIZATION_TRAINING
]);

var GENE_SET_CHARACTERIZATION_DATA_HELP_CONTENT = new HelpContent([
    new HelpContentGroup("Data preparation", [
        new HelpContentElement("List of Identifiers", HelpElementType.HEADING),
        new HelpContentElement("Paste a list of gene/transcript/protein identifiers into the text box, one on each line.", HelpElementType.BODY),
        new HelpContentElement("Gene Set Membership Spreadsheet", HelpElementType.HEADING),
        new HelpContentElement("You may also select or upload a tab-separated spreadsheet file. This allows you to specify multiple gene sets (one per column) at the same time, for parallel analysis. The first row (header) should should contain the names of the gene sets in the corresponding columns. The first column of the spreadsheet should be the gene identifiers corresponding to each row. For each entry in the spreadsheet table, a &ldquo;1&rdquo; indicates that the corresponding row gene is part of the corresponding column gene set, a &ldquo;0&rdquo; means it is not.", HelpElementType.BODY)
    ]),
    new HelpContentGroup("Acceptable gene identifiers", [
        new HelpContentElement("Valid identifiers must describe genes, transcripts, or proteins. Many databases of identifiers are supported including Ensembl, Uniprot, Entrez, HGNC, WikiGene, etc.", HelpElementType.BODY),
    ]),
    GENE_SET_CHARACTERIZATION_TRAINING
]);

var GENE_SET_CHARACTERIZATION_PARAMETERS_HELP_CONTENT = new HelpContent([
    new HelpContentGroup("What is a public gene set?", [
        new HelpContentElement("It is a set of genes with a common property or annotation, such as membership in a specific pathway or functional involvement in a biological process.", HelpElementType.BODY),
    ]),
    new HelpContentGroup("Is &ldquo;Gene Ontology&rdquo; a single gene set?", [
        new HelpContentElement("No, each checkbox is a collection of many public gene sets. When you select a collection, each of its public gene sets will be tested for association with your gene set.", HelpElementType.BODY),
    ]),
    new HelpContentGroup("Where did these public gene sets come from?", [
        new HelpContentElement("Public gene sets are collected from large consortium efforts, such as <a href='http://geneontology.org/' target='_blank'>Gene Ontology</a> and <a href='https://reactome.org/' target='_blank'>Reactome</a>, that collaborate to curate known interactions and annotations of proteins etc.  The public gene sets are also pulled from the most comprehensive, popular databases dedicated to gene set aggregation, such as <a href='http://amp.pharm.mssm.edu/Enrichr/' target='_blank'>Enrichr</a>, <a href='http://software.broadinstitute.org/gsea/msigdb/' target='_blank'>MSigDB</a>, etc.", HelpElementType.BODY),
    ]),
    GENE_SET_CHARACTERIZATION_TRAINING
]);

var GENE_SET_CHARACTERIZATION_NETWORK_HELP_CONTENT = new HelpContent([
    new HelpContentGroup("What does it mean to use the Knowledge Network?", [
        new HelpContentElement("Briefly, the network makes use of known relationships such as protein-protein interactions, genetic interactions and homology relationships among genes. Normally, when you ask whether a property is enriched in your gene set with the Fisher exact test, you count how many genes are actually annotated with that property. When using the Knowledge Network, you additionally consider known biological relationships among genes when approaching the enrichment question. For example, having several genes in your gene set that have PPI relationships with genes in a pathway can add to the evidence that your genes are associated with that pathway. Using the Knowledge Network is our way to make this happen.", HelpElementType.BODY),
    ]),
    new HelpContentGroup("Advantages", [
        new HelpContentElement("This provides a more holistic view of what it means for a gene set to be associated with, say, a well-known pathway. In particular, it looks out for different types of evidence of your genes being linked to the pathway. This may include genes not directly included in the pathway, but closely related to genes in the pathway, e.g., by protein-protein interactions or homology. As a result, it provides a complementary listing of biological processes, pathways, and other annotations enriched in your gene set compared to what you see without the Knowledge Network.", HelpElementType.BODY),
    ]),
    new HelpContentGroup("Disadvantages", [
        new HelpContentElement("This is a novel approach to gene set characterization, showcased in the original <a href='https://www.ncbi.nlm.nih.gov/pubmed/27153592' target='_blank'>DRaWR</a> paper. It has been far less widely used than the standard approach without the Knowledge Network. It is not as straightforward a statistic as the standard approach, and does not provide a p-value of the association.", HelpElementType.BODY),
    ]),
    new HelpContentGroup("What is Network Smoothing?", [
        new HelpContentElement("Network smoothing is the algorithm's probability that controls whether the random walker's next move is to follow a network edge versus to jump back to a node from the query gene set. The higher the network smoothing, the more neighbor information is incorporated into ranking the results. Most often, the network influence is set to a value between 50% and 85% and the results are typically stable within that range.", HelpElementType.BODY),
    ]),
    GENE_SET_CHARACTERIZATION_TRAINING
]);
