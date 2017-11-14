import {Component, OnInit, OnChanges, Input, SimpleChange} from '@angular/core';
import {AbundanceSlider} from './AbundanceSlider';
import {AbundanceTable} from './AbundanceTable';
import {Comparison, CohortPhylumData} from '../../models/mmbdb/CohortComparison';
import {ComparisonNode} from '../../models/mmbdb/ComparisonNode';
import {RadarChart} from './RadarChart';

@Component({
    moduleId: module.id,
    selector: 'relative-abundance',
    templateUrl: './RelativeAbundanceComponent.html',
    styleUrls: ['./RelativeAbundanceComponent.css']
})

export class RelativeAbundanceComponent implements OnInit {
    class = 'relative';

    radarChartInputData: any;
    
    radarConfigOption: RadarConfigOptions;
    
    @Input()
    comparingCohortsPhylumData: Array<CohortPhylumData[]>;

    /** The ComparisonNode objects at the phylum level. */
    @Input()
    comparisonData: ComparisonNode[];
    
    phylumsShownInRadarChart: Array<string> = ["Firmicutes", "Bacteroidetes"];

    /**
     * Number of top OTUs to show.
     */
    @Input()
    topOtuThreshold: number;

    ngOnInit() {
        this.radarChartInputData = this.prepareRadarInputData(this.comparingCohortsPhylumData);
        this.radarConfigOption = this.getRadarConfigOption(50);
    }
    
    onRadiusChange(percentage: number) {
        this.radarConfigOption = this.getRadarConfigOption(percentage);
    }
    
    onSelectedPhylumsChange(selectedPhylums: Array<string>) {
       if (selectedPhylums.length > 0) {
            this.phylumsShownInRadarChart = selectedPhylums;
        } else { 
            //if no phylums are selected, use default
            this.phylumsShownInRadarChart = ["Firmicutes", "Bacteroidetes"];
        }
        this.radarChartInputData = this.prepareRadarInputData(this.comparingCohortsPhylumData);
    }
    
    //generate radar chart input data object
    prepareRadarInputData(abundances: Array<CohortPhylumData[]>) : any {
        var returnVal: any = [];
        if (abundances.length == 3) {
            returnVal.push({
                "group": "baseline",
                "axes": this.prepareRadarInputSubData(abundances[0])
            });
            returnVal.push({
                "group": "cohort 1",
                "axes": this.prepareRadarInputSubData(abundances[1])
            })
            returnVal.push({
                "group": "individual",
                "axes": this.prepareRadarInputSubData(abundances[2])
            })
        }
        return returnVal;
    }
    
    //generte individual cohort's phylum abundances input format
    prepareRadarInputSubData(phylumAbundances: CohortPhylumData[]): any {
        var axes: any = [];
        //var countablePhyla: Array<string> = ["Actinobacteria", "Bacteroidetes", "Fibrobacteres", "Firmicutes", "Fusobacteria",
        //    "Proteobacteria", "Spirochaetes", "Tenericutes", "Verrucomicrobia"];
        var countablePhyla: Array<string> = this.phylumsShownInRadarChart;
        var others: CohortPhylumData[] = [];
        for (var i = 0; i < phylumAbundances.length; i++) {
            if (countablePhyla.indexOf(phylumAbundances[i].node_name) == -1) {
                others.push(phylumAbundances[i]);
            } else {
                // TODO why round to string and then parse to float? there are better ways
                axes.unshift({
                    "axis": phylumAbundances[i].node_name,
                    "value": Number((phylumAbundances[i].relative_abundance_mean * 100).toFixed(2))
                });
            }
        }
        var relative_abundance_mean_others: number = 0;
        for (var j = 0; j < others.length; j++) {
            relative_abundance_mean_others += others[j].relative_abundance_mean * 100;
        }
        // TODO why round to string and then parse to float? there are better ways
        axes.unshift({
            "axis": "Others",
            "value": Number(relative_abundance_mean_others.toFixed(2))
        })
        return axes;
    }
    
    //utility method to create radar chart configuration options.
    getRadarConfigOption(percentage: number): RadarConfigOptions {
         var options: RadarConfigOptions = <RadarConfigOptions> {
            width: 220,
            height: 220,
            paddingX: 156,
            paddingY: 156,
            maxValue: percentage
        };
        return options;
    }
}

export interface RadarConfigOptions {
    //width of the chart
    width: number;
    
    //height of the chart
    height: number;
    
    //chart padding inside of svg 
    paddingX: number;
    
    //chart padding inside of svg
    paddingY: number;
    
    //max percentage value of the axes
    maxValue: number;
}
