import {HelpContent, HelpContentGroup, HelpContentElement, HelpElementType} from '../HelpContent';
import {Pipeline} from '../Pipeline';

export class PhenotypePredictionPipeline extends Pipeline {
    constructor() {
        super(
            "Phenotype Prediction",
            "phenotype_prediction",
            PHENOTYPE_PREDICTION_ABOUT,
            PHENOTYPE_PREDICTION_OVERVIEW_HELP_CONTENT,
            () => {
                return null; // TODO replace
            }
        );
    }
}

var PHENOTYPE_PREDICTION_ABOUT = "You have a spreadsheet of transcriptomic data on a collection of biological samples (or any other &ldquo;omics&rdquo; data set that assigns each gene a numeric value in each sample). You also have a numeric phenotype (e.g., drug response, patient survival, etc.) measurement for each sample. You want to create and understand a model that can predict phenotypic outcomes from the genomic measurements.  This pipeline offers several approaches for creating these models including methods that utilize the relationships between the genomic features that are captured in the Knowledge Network.";

var PHENOTYPE_PREDICTION_OVERVIEW_HELP_CONTENT = new HelpContent([
    new HelpContentGroup("About Phenotype Prediction", [
        new HelpContentElement(PHENOTYPE_PREDICTION_ABOUT, HelpElementType.BODY)
    ])
]);