import {Component, Input, OnChanges, SimpleChange, Output, EventEmitter} from '@angular/core';
import {AbundanceBarChart} from './AbundanceBarChart';
import {AbundanceTopOTU} from './AbundanceTopOTU';
import {AreaChart, CohortDataRecord, AreaChartConfigOptions, AreaChartGraphPoint} from './AreaChart';
import {GroupedBarChart, GroupedBarChartDataRecord, BarDataRecord} from './GroupedBarChart';
import {CohortPhylumData} from '../../models/mmbdb/CohortComparison';
import {ComparisonNode} from '../../models/mmbdb/ComparisonNode';

export interface Abundance {
    phylum: string;
    baselinePerc: number;
    cohort1Perc: number;
    topOTUCount: number;
    individualPerc: number;
    distributions: GroupedBarChartDataRecord[];
    selected: boolean;
}

@Component ({
    moduleId: module.id, 
    selector: 'abundance-table',
    templateUrl: './AbundanceTable.html',
    styleUrls: ['./AbundanceTable.css']
})

export class AbundanceTable implements OnChanges {
    class = 'relative';

    /** abundance objects that fill the table */
    abundances: Abundance[];
    
    /** uncommon abundance objects */
    uncommonAbundances: Abundance[];
    
    /** The string length of the longest phylum-level top OTU count. */
    maxOtuLength: number = 0;
    
    /** clickable the minus/plus image to expand/close the uncommon phylum */
    uncommonPhylumImageSrc: string = "img/mmbdb/plus.png";
    
    /** expand/close uncommon phylum in the table*/
    showUncommonPhylum: boolean = false;

    @Input()
    abundanceData: Array<CohortPhylumData[]>;

    /** The ComparisonNode objects at the phylum level. */
    @Input()
    comparisonData: ComparisonNode[];

    /**
     * Number of top OTUs to show.
     */
    @Input()
    topOtuThreshold: number;
    
    /**
     * Emits event that contains selected phylums to draw radar chart axes
     */
    @Output()
    selectedPhylums: EventEmitter<Array<string>> = new EventEmitter<Array<string>>();

    ngOnChanges(changes: {[propertyName: string]: SimpleChange}) {
        this.abundances = this.prepareTableInputData();
    }

    //Assume baseline, variant and individual have same set of phylums and they appear in alphabetical order
    prepareTableInputData(): Abundance[] {
        var returnVal: Abundance[] = [];
        this.uncommonAbundances = [];
        var countablePhyla: Array<string> = ["Actinobacteria", "Bacteroidetes", "Fibrobacteres", "Firmicutes", "Fusobacteria",
            "Proteobacteria", "Spirochaetes", "Tenericutes", "Verrucomicrobia"]
        var baselineOthers: Array<CohortPhylumData> = [];
        var variantOthers: Array<CohortPhylumData> = [];
        var individualOthers: Array<CohortPhylumData> = [];
        var topOTUCountOthers: number = 0;

        // map from phylum name to top OTU count
        var phylumNameToOtuCount: any = d3.map({});
        if (this.comparisonData !== null) {
            this.maxOtuLength = 0;
            this.comparisonData.forEach((node) => {
                var count: number = node.getNumTopOtus(this.topOtuThreshold);
                phylumNameToOtuCount.set(node.name, count);
                this.maxOtuLength = Math.max(this.maxOtuLength, count.toString().length);
            });
        }

        if (this.abundanceData && this.abundanceData.length == 3) {
            for (var i = 0; i < this.abundanceData[0].length; i++) {
                var name: string = this.abundanceData[0][i].node_name;
                if (countablePhyla.indexOf(name) == -1) {
                    baselineOthers.push(this.abundanceData[0][i]);
                    variantOthers.push(this.abundanceData[1][i]);
                    individualOthers.push(this.abundanceData[2][i]);
                    topOTUCountOthers += (phylumNameToOtuCount.get(name) || 0);
                    // TODO why round to string and then parse to float? there are better ways
                    this.uncommonAbundances.push({
                        "phylum": name,
                        "baselinePerc": Number((this.abundanceData[0][i].relative_abundance_mean * 100).toFixed(1)),
                        "cohort1Perc": Number((this.abundanceData[1][i].relative_abundance_mean * 100).toFixed(1)),
                        "topOTUCount": (phylumNameToOtuCount.get(name) || 0),
                        "individualPerc": Number((this.abundanceData[2][i].relative_abundance_mean * 100).toFixed(1)),
                        "distributions": this.prepareDistributionData([this.abundanceData[0][i], this.abundanceData[1][i], this.abundanceData[2][i]]),
                        "selected": false
                    });
                } else {
                    // TODO why round to string and then parse to float? there are better ways
                    returnVal.push({
                        "phylum": name,
                        "baselinePerc": Number((this.abundanceData[0][i].relative_abundance_mean * 100).toFixed(1)),
                        "cohort1Perc": Number((this.abundanceData[1][i].relative_abundance_mean * 100).toFixed(1)),
                        "topOTUCount": (phylumNameToOtuCount.get(name) || 0),
                        "individualPerc": Number((this.abundanceData[2][i].relative_abundance_mean * 100).toFixed(1)),
                        "distributions": this.prepareDistributionData([this.abundanceData[0][i], this.abundanceData[1][i], this.abundanceData[2][i]]),
                        "selected": this.isDefaultPhylumShownInRadarChart(name)
                    });
                }
            }
        }
        //sum up the "Others" phyla
        var relative_abundance_mean_baselineOthers: number = 0;
        var relative_abundance_mean_variantOthers: number = 0;
        var relative_abundance_mean_individualOthers: number = 0;
        for (var i = 0; i < baselineOthers.length; i++) {
            relative_abundance_mean_baselineOthers += baselineOthers[i].relative_abundance_mean * 100
        }
        for (var i = 0; i < variantOthers.length; i++) {
            relative_abundance_mean_variantOthers += variantOthers[i].relative_abundance_mean * 100
        }
        for (var i = 0; i < individualOthers.length; i++) {
            relative_abundance_mean_individualOthers += individualOthers[i].relative_abundance_mean * 100
        }
        var baselinePercOthers: string = relative_abundance_mean_baselineOthers.toFixed(1);
        var cohort1PercOthers: string = relative_abundance_mean_variantOthers.toFixed(1);
        var individualPercOthers: string = relative_abundance_mean_individualOthers.toFixed(1);
        returnVal.push({
            "phylum": "Uncommon",
            "baselinePerc": Number(baselinePercOthers),
            "cohort1Perc": Number(cohort1PercOthers),
            "topOTUCount": topOTUCountOthers,
            "individualPerc": Number(individualPercOthers),
            "distributions": [], 
            "selected": false
        });
        return returnVal;
    }

    /**
     * Construct the input structure for the eight or nine phyla that researchers are interested in, like Bacteroisetes, Firmucutes etc.
     */
    prepareDistributionData(relativeAbundances: Array<CohortPhylumData>): Array<GroupedBarChartDataRecord> {
        var returnVal: Array<GroupedBarChartDataRecord> = [];
        if (relativeAbundances && relativeAbundances.length == 3) {
            var barDataRecordsAtZero: BarDataRecord[] = [];
            barDataRecordsAtZero.push({
                "cohort": "Baseline",
                "sampleSize": relativeAbundances[0].relative_abundance_histo_num_zeros
            });
            barDataRecordsAtZero.push({
                "cohort": "Cohort 1",
                "sampleSize": relativeAbundances[1].relative_abundance_histo_num_zeros
            });
            barDataRecordsAtZero.push({
                "cohort": "Individual",
                "sampleSize": relativeAbundances[2].relative_abundance_histo_num_zeros
            });
            returnVal.push({
                "binName": "0",
                "barDataRecords": barDataRecordsAtZero
            });
            for (var i = 0; i < relativeAbundances[0].relative_abundance_histo_bin_height_y.length; i++) {
                var barDataRecords: BarDataRecord[] = [];
                barDataRecords.push({
                    "cohort": "Baseline",
                    "sampleSize": relativeAbundances[0].relative_abundance_histo_bin_height_y[i]
                });
                barDataRecords.push({
                    "cohort": "Cohort 1",
                    "sampleSize": relativeAbundances[1].relative_abundance_histo_bin_height_y[i]
                });
                barDataRecords.push({
                    "cohort": "Individual",
                    "sampleSize": relativeAbundances[2].relative_abundance_histo_bin_height_y[i]
                })
                var binName: string = '';
                if (i == 0)
                    binName = "(" + (relativeAbundances[0].relative_abundance_histo_bin_start_x[i] * 100).toFixed(0) + "-" + (relativeAbundances[0].relative_abundance_histo_bin_end_x[i] * 100).toFixed(0) + ")";
                else if (i == relativeAbundances[0].relative_abundance_histo_bin_height_y.length - 1)
                    binName = "[" + (relativeAbundances[0].relative_abundance_histo_bin_start_x[i] * 100).toFixed(0) + "-" + (relativeAbundances[0].relative_abundance_histo_bin_end_x[i] * 100).toFixed(0) + "]";
                else
                    binName = "[" + (relativeAbundances[0].relative_abundance_histo_bin_start_x[i] * 100).toFixed(0) + "-" + (relativeAbundances[0].relative_abundance_histo_bin_end_x[i] * 100).toFixed(0) + ")";
                returnVal.push({
                    "binName": binName,
                    "barDataRecords": barDataRecords
                })
            }
        }
        return returnVal;
    }
    
    /** By default, we will show firmicutes and bacteroidetes as selected phylums in the table */
    isDefaultPhylumShownInRadarChart(phylum: string): boolean {
       if (phylum == "Firmicutes" || phylum == "Bacteroidetes")
            return true;
        else
            return false;
    }
    
    /** when checkboxes are checked/unchecked, emit an event that contains selected phylum so event listener, the radar chart in this case, will react to the event */
    onCheckboxChange(abundance: Abundance) : void {
        abundance.selected = (abundance.selected) ? false : true;
        var selected: Array<string> = [];
        for (var i = 0; i < this.abundances.length; i++) {
            if (this.abundances[i].selected) {
                selected.push(this.abundances[i].phylum);
            }
        }
        for (var j = 0; j < this.uncommonAbundances.length; j++) {
            if (this.uncommonAbundances[j].selected) {
                selected.push(this.uncommonAbundances[j].phylum);
            }
        }
        this.selectedPhylums.emit(selected);     
    }
    
    /** change the expand/close image to close/expand when it is clicked */
    changeImage() : void {
        this.uncommonPhylumImageSrc = (this.uncommonPhylumImageSrc == "img/mmbdb/plus.png") ? "img/mmbdb/minus.png" : "img/mmbdb/plus.png"; 
        this.showUncommonPhylum = (this.uncommonPhylumImageSrc == "img/mmbdb/plus.png") ? false : true;
    }
}
