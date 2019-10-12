import 'rxjs/add/observable/forkJoin';
import {Observable} from 'rxjs/Observable';

import {HelpContent, HelpContentGroup, HelpContentElement, HelpElementType} from '../HelpContent';
import {Form, FormGroup, FormField, FileFormField, VALID_UNLESS_REQUIRED_BUT_EMPTY, VALID_NUMBER, ALWAYS} from '../Form';
import {Pipeline} from '../Pipeline';
import {FileService} from '../../../services/knoweng/FileService';
import {JobService} from '../../../services/knoweng/JobService';

export class SpreadsheetVisualizationPipeline extends Pipeline {

    constructor(private fileService: FileService, private jobService: JobService) {
        super(
            "Spreadsheet Visualization",
            "spreadsheet_visualization",
            SPREADSHEET_VISUALIZATION_ABOUT,
            SPREADSHEET_VISUALIZATION_OVERVIEW_HELP_CONTENT,
            () => {
                return Observable.from([new Form("spreadsheet_visualization", [
                        new FormGroup("Data", SPREADSHEET_VISUALIZATION_DATA_HELP_CONTENT, [
                            new FileFormField("spreadsheets", null, null, "Select one or more spreadsheets.", "Spreadsheet File(s)", true, null, this.fileService, this.jobService, true, false, VALID_UNLESS_REQUIRED_BUT_EMPTY, ALWAYS, true)
                        ])])]
                    );
            }
        );
    }
}

var SPREADSHEET_VISUALIZATION_ABOUT = "The Spreadsheet Visualization pipeline allows users to visually compare " +
    "multiple spreadsheets of related data to discover relationships between features and groups among the samples. " +
    "Once the pipeline is run, the results can be opened into the visualization module that allows users to " +
    "interactively compare the spreadsheets in a single view.";

var SPREADSHEET_VISUALIZATION_TRAINING = new HelpContentGroup("Info and training", [
    new HelpContentElement("Quickstart Guide", HelpElementType.HEADING),
    new HelpContentElement("This guide walks you through the entire pipeline from setup to visualization of results. It also includes links to sample data.", HelpElementType.BODY),
    new HelpContentElement("<a href='https://knoweng.org/quick-start/' target='_blank'>Download the Spreadsheet Visualization Quickstart Guide PDF</a>", HelpElementType.BODY),
    new HelpContentElement("Video Tutorials", HelpElementType.HEADING),
    new HelpContentElement("The KnowEnG YouTube Channel contains videos for every pipeline (some currently in development) as well as information about unique attributes of the KnowEnG Platform.", HelpElementType.BODY),
    new HelpContentElement("<a href='https://www.youtube.com/channel/UCjyIIolCaZIGtZC20XLBOyg' target='_blank'>Visit the KnowEnG YouTube Channel</a>", HelpElementType.BODY)
]);

var SPREADSHEET_VISUALIZATION_OVERVIEW_HELP_CONTENT = new HelpContent([
    new HelpContentGroup("About Spreadsheet Visualization", [
        new HelpContentElement(SPREADSHEET_VISUALIZATION_ABOUT, HelpElementType.BODY)
    ]),
    // TODO SPREADSHEET_VISUALIZATION_TRAINING
]);

var SPREADSHEET_VISUALIZATION_DATA_HELP_CONTENT = new HelpContent([
    new HelpContentGroup("What should I use as spreadsheets?", [
        new HelpContentElement("The spreadsheet visualizer can be run with multiple spreadsheets or with a single spreadsheet.", HelpElementType.BODY),
        new HelpContentElement("Multiple Spreadsheets (recommended)", HelpElementType.HEADING),
        new HelpContentElement("When using multiple spreadsheets, each spreadsheet must represent the same sample population. " +
            "Spreadsheet orientation does not matter&mdash;that is, samples can correspond to rows or to columns&mdash;as long " +
            "as the sample identifiers are consistent between files and all files have at least 50% of their samples in common. " +
            "It is best to separate different data types into their own spreadsheets. For example, if you have gene-expression data, " +
            "somatic mutation data, and clinical data, the spreadsheet visualizer will be most effective if the data are organized " +
            "as three spreadsheets, one containing the gene-expression data, one containing the somatic mutation data, and one " +
            "containing the clinical data.", HelpElementType.BODY),
        new HelpContentElement("Single Spreadsheet", HelpElementType.HEADING),
        new HelpContentElement("When using a single spreadsheet, it is best if the spreadsheet is oriented such that " +
            "columns correspond to samples.", HelpElementType.BODY)
    ]),
    // TODO SPREADSHEET_VISUALIZATION_TRAINING
]);
