export class Cohort {
    constructor(
        public _id: number,
        public display_name_short: string,
        public display_name_long: string,
        public num_samples: number) {
    }
}

export class Comparison {
    constructor(
        public _id: number,
        public display_name: string,
        public baseline_cohort_id: number,
        public variant_cohort_id: number,
        public patient_cohort_id: number,
        public top_fst_ranked_otu_scores: number[]) {
    }
    
}

//probably we don't need a constructor since we don't modify data in anyway when reading this from API 
export class CohortPhylumData {
    _id: number;
    cohort_id: number;
    node_name: string;
    
    relative_abundance_mean: number;
    relative_abundance_histo_num_zeros: number;
    relative_abundance_histo_bin_height_y: Array<number>;
    relative_abundance_histo_bin_start_x: Array<number>;
    relative_abundance_histo_bin_end_x: Array<number>;
   
    num_unique_otus_histo_num_zeros: number;
    num_unique_otus_mean: number;
    num_unique_otus_histo_bin_height_y: Array<number>;
    num_unique_otus_histo_bin_start_x: Array<number>;
    num_unique_otus_histo_bin_end_x: Array<number>;
    
    normalized_entropy_histo_num_zeros: number;
    normalized_entropy_mean: number;
    normalized_entropy_histo_bin_start_x: Array<number>;
    normalized_entropy_histo_bin_end_x: Array<number>;
    normalized_entropy_histo_bin_height_y: Array<number>
   

}
