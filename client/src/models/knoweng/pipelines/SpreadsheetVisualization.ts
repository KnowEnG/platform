import 'rxjs/add/observable/forkJoin';
import {Observable} from 'rxjs/Observable';

import {HelpContent, HelpContentGroup, HelpContentElement, HelpElementType} from '../HelpContent';
import {Form, FormGroup, FormField, FileFormField, VALID_UNLESS_REQUIRED_BUT_EMPTY, VALID_NUMBER, ALWAYS} from '../Form';
import {Pipeline} from '../Pipeline';
import {FileService} from '../../../services/knoweng/FileService';

export class SpreadsheetVisualizationPipeline extends Pipeline {

    constructor(private fileService: FileService) {
        super(
            "Spreadsheet Visualization",
            "spreadsheet_visualization",
            SPREADSHEET_VISUALIZATION_ABOUT,
            SPREADSHEET_VISUALIZATION_OVERVIEW_HELP_CONTENT,
            () => {
                return Observable.from([new Form("spreadsheet_visualization", [
                        new FormGroup("Primary Spreadsheet", SPREADSHEET_VISUALIZATION_PRIMARY_FILE_HELP_CONTENT, [
                            new FileFormField("primary_file", null, null, "Select the Primary Spreadsheet", "Primary File", true, null, this.fileService, true, false, VALID_UNLESS_REQUIRED_BUT_EMPTY, ALWAYS)
                        ]),
                        new FormGroup("Secondary Spreadsheet(s)", SPREADSHEET_VISUALIZATION_SECONDARY_FILE_HELP_CONTENT, [
                            new FileFormField("secondary_files", null, null, "Select the Secondary Spreadsheet(s)", "Secondary Files", true, null, this.fileService, true, false, VALID_UNLESS_REQUIRED_BUT_EMPTY, ALWAYS)
                        ])])]
                    );
            }
        );
    }
}

var SPREADSHEET_VISUALIZATION_ABOUT = "The Spreadsheet Visualization pipeline allows users to visually compare multiple spreadsheets of related data to discover correlations between features and groups within the data. Primary and Secondary spreadsheets are designed in the pipeline setup. Once the pipeline is run, the results can be opened into the visualization module that allows users to interactively compare these data sets in a single view.";

var SPREADSHEET_VISUALIZATION_TRAINING = new HelpContentGroup("Info and training", [
    new HelpContentElement("Quickstart Guide", HelpElementType.HEADING),
    new HelpContentElement("This guide walks you through the entire pipeline from setup to visualization of results. It also includes links to sample data.", HelpElementType.BODY),
    new HelpContentElement("<a href='//www.knoweng.org/quick-start/' target='_blank'>Download the Spreadsheet Visualization Quickstart Guide PDF</a>", HelpElementType.BODY),
    new HelpContentElement("Video Tutorials", HelpElementType.HEADING),
    new HelpContentElement("The KnowEnG YouTube Channel contains videos for every pipeline (some currently in development) as well as information about unique attributes of the KnowEnG Platform.", HelpElementType.BODY),
    new HelpContentElement("<a href='//www.youtube.com/channel/UCjyIIolCaZIGtZC20XLBOyg' target='_blank'>Visit the KnowEnG YouTube Channel</a>", HelpElementType.BODY)
]);

var SPREADSHEET_VISUALIZATION_OVERVIEW_HELP_CONTENT = new HelpContent([
    new HelpContentGroup("About Spreadsheet Visualization", [
        new HelpContentElement(SPREADSHEET_VISUALIZATION_ABOUT, HelpElementType.BODY)
    ]),
    SPREADSHEET_VISUALIZATION_TRAINING
]);

var SPREADSHEET_VISUALIZATION_PRIMARY_FILE_HELP_CONTENT = new HelpContent([
    new HelpContentGroup("What should I use as the Primary Spreadsheet?", [
        new HelpContentElement("The primary Spreadsheet should be a data file to which you want to compare other (possibly multiple other) data spreadsheets. Typically, the Primary Spreadsheet will be a file containing genotypic data.", HelpElementType.BODY)
    ]),
    SPREADSHEET_VISUALIZATION_TRAINING
]);

var SPREADSHEET_VISUALIZATION_SECONDARY_FILE_HELP_CONTENT = new HelpContent([
    new HelpContentGroup("What should I use as the Secondary Spreadsheet(s)?", [
        new HelpContentElement("The Secondary Spreadsheet(s) are those data sets that you wish to view in the context of your Primary Spreadsheet or data set. Typically, the Secondary Spreadsheet(s) will be files containingg phenotypic data that is linked to your genotypic spreadsheet. But it also could include a spreadsheet that identifies cluster IDs from other analysis that have been performed or any other metadata that is linked to your Primary Spreadsheet.", HelpElementType.BODY)
    ]),
    SPREADSHEET_VISUALIZATION_TRAINING
]);
