import {Component, OnInit} from '@angular/core';
import {Router, ActivatedRoute, Params} from '@angular/router';
import {tokenNotExpired} from 'angular2-jwt'

import {CohortComparisonService} from '../../services/mmbdb/CohortComparisonService';
import {CohortNodeService} from '../../services/mmbdb/CohortNodeService';
import {Comparison, CohortPhylumData, Cohort} from '../../models/mmbdb/CohortComparison';
import {ComparisonNode} from '../../models/mmbdb/ComparisonNode';
import {ComparisonNodeService} from '../../services/mmbdb/ComparisonNodeService';
import {ThresholdPickerService} from '../../services/common/ThresholdPickerService';

@Component({
    moduleId: module.id,
    selector: 'cohort-comparison',
    templateUrl: './CohortComparisonTool.html',
    styleUrls: ['./CohortComparisonTool.css'],
    providers: [CohortComparisonService, CohortNodeService, ComparisonNodeService, ThresholdPickerService]
})

export class CohortComparisonTool implements OnInit{
    class = 'relative';
    
    loadingComparison: boolean = true;
    
    loadingPhylumData: boolean = true;
    
    loadingNodeData: boolean = true;
    
    loadingCohortData: boolean = true;
    
    baselineCohort: Cohort;
    
    variantCohort: Cohort;
    
    individual: Cohort;
    
    displayedComparisonName: string;

    selectedId: number;
    
    comparison: Comparison;

    topOtuThreshold: number;

    //this includes relative abundance, richness, evenness data for all phyla included in all cohorts in this comparison
    comparingCohortsPhylumData: Array<CohortPhylumData[]>;

    /** The ComparisonNode objects at the phylum level. */
    comparisonData: ComparisonNode[];

    constructor(private router: Router,
        private route: ActivatedRoute,
        public cohortComparisonService: CohortComparisonService,
        public comparisonNodeService: ComparisonNodeService,
        public thresholdPickerService: ThresholdPickerService) {

        this.topOtuThreshold =
            this.thresholdPickerService.numIncludedStream.getValue();
        this.thresholdPickerService.numIncludedStream.subscribe(
            (numIncluded: number) => {
                if (numIncluded != this.topOtuThreshold) {
                    this.topOtuThreshold = numIncluded;
                }
            },
            (error: any) => {
                alert(`Server error. Try again later`);
            }
        );
    }

    ngOnInit() {
        this.route.params
            .subscribe((params: Params) => {
                this.loadingPhylumData = true;
                this.loadingNodeData = true;
                this.loadingCohortData = true;
                this.loadingComparison = true;
                this.selectedId = params['id'];
                this.getComparison(this.selectedId);
            });
    }

    /**
     * Read comparison from API
     */
    getComparison(comparisonId: number) {
        //read the sample comparison and find compared cohort ids from the comparison from API
        if (comparisonId /*&& comparisonId != ''*/) {
            this.cohortComparisonService.getComparison(comparisonId)
               .subscribe((comparison: Comparison) => {
                    this.comparison = comparison;
                    this.loadingComparison = false;
                    this.getComparingCohorts(comparison);
                },
                (err: any) => {
                    alert(err);
                    this.loadingPhylumData = false;
                });
            this.comparisonNodeService.getNodesForLevels(comparisonId, ['phylum'])
                .subscribe((comparisonNodes: ComparisonNode[]) => {
                    // TODO unify services and models; have some redundant code,
                    // API calls, and in-memory data
                    this.comparisonData = comparisonNodes;
                    this.loadingNodeData = false;
                },
                (err: any) => {
                    alert(err);
                    this.loadingNodeData = false;
                });
        }
    }
    
    /**
     * Read comparing cohorts and cohort phylum data from API
     **/
    getComparingCohorts(comparison: Comparison) {
        if (comparison) {
            var baseline_cohort_id = comparison.baseline_cohort_id;
            var variant_cohort_id = comparison.variant_cohort_id;
            var patient_cohort_id = comparison.patient_cohort_id;
            if (baseline_cohort_id && variant_cohort_id && patient_cohort_id) {
                var cohortIDs = [baseline_cohort_id, variant_cohort_id, patient_cohort_id];
                this.cohortComparisonService.getAllComparingCohorts(cohortIDs).subscribe(
                    (data: any) => {
                        this.baselineCohort = data[0];
                        this.variantCohort = data[1];
                        this.individual = data[2];
                        this.loadingCohortData = false;
                    }
                );
                this.cohortComparisonService.getAllComparingCohortPhylumTreeData(cohortIDs).subscribe(
                    (data: any) => {
                        var baselinePhylumData: CohortPhylumData[] = data[0];
                        var variantPhylumData: CohortPhylumData[] = data[1];
                        var patientPhylumData: CohortPhylumData[] = data[2];
                        this.comparingCohortsPhylumData = [baselinePhylumData, variantPhylumData, patientPhylumData];
                        this.loadingPhylumData = false;
                    },
                    (err: any) => {
                        alert(err);
                        this.loadingPhylumData = false;
                    }
                );
            }
        }
    }
}
