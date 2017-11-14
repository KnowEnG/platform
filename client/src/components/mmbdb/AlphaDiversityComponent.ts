import {Component, OnChanges, Input, SimpleChange} from '@angular/core';
import {RichnessTable} from "./RichnessTable";
import {EvennessTable} from "./EvennessTable";
import {AreaChart, CohortDataRecord, AreaChartConfigOptions, AreaChartGraphPoint} from "./AreaChart";
import {CohortPhylumData, Cohort} from '../../models/mmbdb/CohortComparison';
import {CohortComparisonService} from '../../services/mmbdb/CohortComparisonService';
import {GroupedBarChart, GroupedBarChartDataRecord, BarDataRecord} from './GroupedBarChart';

@Component ({
    moduleId: module.id,
    selector: 'alpha-diversity',
    templateUrl: './AlphaDiversityComponent.html',
    styleUrls: ['./AlphaDiversityComponent.css']
})

export class AlphaDiversityComponent implements OnChanges{
    class = 'relative';
    
    richnessData: GroupedBarChartDataRecord[];
    
    maxRichness: string;
    
    maxEvenness: string;
    
    evennessData: GroupedBarChartDataRecord[];
    
    individualRichnessScore: string;
    
    individualEvennessScore: string;
    
    @Input()
    individual: Cohort;
    
    @Input()
    comparingCohortsPhylumData: Array<CohortPhylumData[]>;
    
    constructor(public cohortComparisonService: CohortComparisonService) {
    }
    
    ngOnChanges(changes: {[propKey: string]: SimpleChange}) {
        var comparingCohortsIDs = this.getComparingCohortIDs();
        this.getCohortPhyloTreeRootData(comparingCohortsIDs);
    }
    
    //find the cohort ids to pass to API endpoint to retrieve richness data
    getComparingCohortIDs(): Array<string> {
        var cohortIDs: Array<string> = [];
        for (var i = 0; i < this.comparingCohortsPhylumData.length; i++) {
            cohortIDs.push(this.comparingCohortsPhylumData[i][0].cohort_id);
        }
        return cohortIDs;
    }
    
    //Call API to read richness and evenness data for all comparing cohorts, currently assuming there are only two cohorts
    getCohortPhyloTreeRootData(cohortIDs: Array<string>) {
        this.cohortComparisonService.getAllComparingCohortsRootData(cohortIDs)
            .subscribe ( 
                (data: any) => {
                    var baselineData: CohortPhylumData[] = data[0];
                    var variantData: CohortPhylumData[] = data[1];
                    var individualData: CohortPhylumData[] = data[2];
                    this.richnessData = this.prepareRichnessHistoData([baselineData, variantData, individualData]);
                    this.evennessData = this.prepareEvennessHistoData([baselineData, variantData, individualData]);
                    this.individualRichnessScore = individualData[0].num_unique_otus_mean.toFixed(0);
                    this.individualEvennessScore = individualData[0].normalized_entropy_mean.toFixed(2);
                }
             );
    }
    
    prepareRichnessHistoData(richnesses: Array<CohortPhylumData[]>): GroupedBarChartDataRecord[] {
        var returnVal: Array<GroupedBarChartDataRecord> = [];
        if (richnesses && richnesses.length == 3) {
            var barDataRecordsAtZero: BarDataRecord[] = [];
            barDataRecordsAtZero.push({
                "cohort": "Baseline",
                "sampleSize": richnesses[0][0].num_unique_otus_histo_num_zeros
            });
            barDataRecordsAtZero.push({
                "cohort": "Cohort 1",
                "sampleSize": richnesses[1][0].num_unique_otus_histo_num_zeros
            });
            barDataRecordsAtZero.push({
                "cohort": "Individual",
                "sampleSize": richnesses[2][0].num_unique_otus_histo_num_zeros
            });
            returnVal.push({
                "binName": "0",
                "barDataRecords": barDataRecordsAtZero
            });
            for (var i = 0; i < richnesses[0][0].num_unique_otus_histo_bin_height_y.length; i++) {
                var barDataRecords: BarDataRecord[] = [];
                barDataRecords.push({
                    "cohort": "Baseline",
                    "sampleSize": richnesses[0][0].num_unique_otus_histo_bin_height_y[i]
                });
                barDataRecords.push({
                    "cohort": "Cohort 1",
                    "sampleSize": richnesses[1][0].num_unique_otus_histo_bin_height_y[i]
                });
                barDataRecords.push({
                    "cohort": "Individual",
                    "sampleSize": richnesses[2][0].num_unique_otus_histo_bin_height_y[i]
                })
                var binName: string = '';
                if (i == 0)
                    binName = "(" + (richnesses[0][0].num_unique_otus_histo_bin_start_x[i]).toFixed(0) + "-" + (richnesses[0][0].num_unique_otus_histo_bin_end_x[i]).toFixed(0) + ")";
                else if (i == richnesses[0][0].num_unique_otus_histo_bin_height_y.length - 1) {
                    binName = "[" + (richnesses[0][0].num_unique_otus_histo_bin_start_x[i]).toFixed(0) + "-" + (richnesses[0][0].num_unique_otus_histo_bin_end_x[i]).toFixed(0) + "]";
                    this.maxRichness = (richnesses[0][0].num_unique_otus_histo_bin_end_x[i]).toFixed(0);
                } else
                    binName = "[" + (richnesses[0][0].num_unique_otus_histo_bin_start_x[i]).toFixed(0) + "-" + (richnesses[0][0].num_unique_otus_histo_bin_end_x[i]).toFixed(0) + ")";
                returnVal.push({
                    "binName": binName,
                    "barDataRecords": barDataRecords
                })
            }
        }
        return returnVal;
    }
    
     prepareEvennessHistoData(evennesses: Array<CohortPhylumData[]>): GroupedBarChartDataRecord[] {
        var returnVal: Array<GroupedBarChartDataRecord> = [];
        if (evennesses && evennesses.length == 3) {
            var barDataRecordsAtZero: BarDataRecord[] = [];
            barDataRecordsAtZero.push({
                "cohort": "Baseline",
                "sampleSize": evennesses[0][0].normalized_entropy_histo_num_zeros
            });
            barDataRecordsAtZero.push({
                "cohort": "Cohort 1",
                "sampleSize": evennesses[1][0].normalized_entropy_histo_num_zeros
            });
            barDataRecordsAtZero.push({
                "cohort": "Individual",
                "sampleSize": evennesses[2][0].normalized_entropy_histo_num_zeros
            });
            returnVal.push({
                "binName": "0",
                "barDataRecords": barDataRecordsAtZero
            });
            for (var i = 0; i < evennesses[0][0].normalized_entropy_histo_bin_height_y.length; i++) {
                var barDataRecords: BarDataRecord[] = [];
                barDataRecords.push({
                    "cohort": "Baseline",
                    "sampleSize": evennesses[0][0].normalized_entropy_histo_bin_height_y[i]
                });
                barDataRecords.push({
                    "cohort": "Cohort 1",
                    "sampleSize": evennesses[1][0].normalized_entropy_histo_bin_height_y[i]
                });
                barDataRecords.push({
                    "cohort": "Individual",
                    "sampleSize": evennesses[2][0].normalized_entropy_histo_bin_height_y[i]
                })
                var binName: string = '';
                if (i == 0)
                    binName = "(" + (evennesses[0][0].normalized_entropy_histo_bin_start_x[i]).toFixed(2) + "-" + (evennesses[0][0].normalized_entropy_histo_bin_end_x[i]).toFixed(2) + ")";
                else if (i == evennesses[0][0].normalized_entropy_histo_bin_height_y.length - 1) {
                    binName = "[" + (evennesses[0][0].normalized_entropy_histo_bin_start_x[i]).toFixed(2) + "-" + (evennesses[0][0].normalized_entropy_histo_bin_end_x[i]).toFixed(2) + "]";
                    this.maxEvenness = (evennesses[0][0].normalized_entropy_histo_bin_end_x[i]).toFixed(2);
                } else
                    binName = "[" + (evennesses[0][0].normalized_entropy_histo_bin_start_x[i]).toFixed(2) + "-" + (evennesses[0][0].normalized_entropy_histo_bin_end_x[i]).toFixed(2) + ")";
                returnVal.push({
                    "binName": binName,
                    "barDataRecords": barDataRecords
                })
            }
        }
        return returnVal;
    }
}