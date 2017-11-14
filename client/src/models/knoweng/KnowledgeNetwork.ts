/**
 * Model class for "Select interaction network for analysis" dropdown list of the pipelines' launcher 
 */
export class AnalysisNetwork {
    constructor(
        public _id: number,
        public analysis_network_name: string,
        public species_number: string, // TODO in the future, string or number?
        public edge_type_name: string,
        public selected_by_default: boolean) {
    }
}

/**
 * Model class for "Choose public gene sets for comparison" in the dropdown list of Gene Set Characterization pipeline launcher
 */
export class Collection {
    constructor(
        public _id: number,
        public super_collection: string,
        public species_number: string, // TODO in the future, string or number?
        public edge_type_name: string,
        public super_collection_display_index: number,
        public collection: string,
        public collection_selected_by_default: boolean) {
    }
}

/**
 * Model class for "Select species" in the dropdown list of the pipeline launcher 
 */
export class Species {
    constructor(
        public _id: number,
        public name: string,
        public short_latin_name: string,
        public species_number: string,
        public group_name: string,
        public display_order: number,
        public selected_by_default: boolean) {
    }
}
