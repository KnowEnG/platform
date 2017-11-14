import {Component, OnInit, Input} from '@angular/core';
import {AreaChart, CohortDataRecord, AreaChartConfigOptions, AreaChartGraphPoint} from './AreaChart';
import {CohortPhylumData} from '../../models/mmbdb/CohortComparison';
import {GroupedBarChart, GroupedBarChartDataRecord, BarDataRecord} from './GroupedBarChart';

export interface Richness {
    phylum: string;
    data: GroupedBarChartDataRecord[];
}

@Component ({
    moduleId: module.id,
    selector: 'richness-table',
    templateUrl: './RichnessTable.html',
    styleUrls: ['./RichnessEvennessTable.css']
})

export class RichnessTable implements OnInit{
 class = 'relative';
    
    richnessesPartOne: Richness[] = [];
    
    richnessesPartTwo: Richness[] = [];
    
    firstBinName: string = '';
    
    maxXLabel: string = '';
    
    @Input()
    comparingCohortsPhylumData: Array<CohortPhylumData[]>;
    
    ngOnInit() {
        this.prepareRichnessData();
    }
    
    prepareRichnessData() {
       if (this.comparingCohortsPhylumData.length == 3) {
           for (var i = 0; i < this.comparingCohortsPhylumData[0].length; i++) {
               var countablePhylaPartOne: Array<string> = ["Actinobacteria", "Bacteroidetes", "Fibrobacteres", "Firmicutes", "Fusobacteria"];
               var countablePhylaPartTwo: Array<string> = ["Proteobacteria", "Spirochaetes", "Tenericutes", "Verrucomicrobia"];
               if (countablePhylaPartOne.indexOf(this.comparingCohortsPhylumData[0][i].node_name) != -1
                  || countablePhylaPartTwo.indexOf(this.comparingCohortsPhylumData[0][i].node_name) != -1) {
                   var data: GroupedBarChartDataRecord[] = [];
                   var barDataRecordsAtZero: BarDataRecord[] = [];
                   barDataRecordsAtZero.push({
                       "cohort": "Baseline",
                       "sampleSize": this.comparingCohortsPhylumData[0][i].num_unique_otus_histo_num_zeros
                   });
                   barDataRecordsAtZero.push({
                       "cohort": "Cohort 1",
                       "sampleSize": this.comparingCohortsPhylumData[1][i].num_unique_otus_histo_num_zeros
                   });
                   barDataRecordsAtZero.push({
                       "cohort": "Individual",
                       "sampleSize": this.comparingCohortsPhylumData[2][i].num_unique_otus_histo_num_zeros
                   });
                   data.push({
                       "binName": "0",
                       "barDataRecords": barDataRecordsAtZero
                   });
                   for (var j = 0; j < this.comparingCohortsPhylumData[0][i].num_unique_otus_histo_bin_height_y.length; j++) {
                       var barDataRecords: BarDataRecord[] = [];
                       barDataRecords.push({
                           "cohort": "Baseline",
                           "sampleSize": this.comparingCohortsPhylumData[0][i].num_unique_otus_histo_bin_height_y[j]
                       });
                       barDataRecords.push({
                           "cohort": "Cohort 1",
                           "sampleSize": this.comparingCohortsPhylumData[1][i].num_unique_otus_histo_bin_height_y[j]
                       });
                       barDataRecords.push({
                           "cohort": "Individual",
                           "sampleSize": this.comparingCohortsPhylumData[2][i].num_unique_otus_histo_bin_height_y[j]
                       })
                       var binName: string = '';
                       if (j == 0) {
                           binName = "(" + (this.comparingCohortsPhylumData[0][i].num_unique_otus_histo_bin_start_x[j]).toFixed(0) + "-" + (this.comparingCohortsPhylumData[0][i].num_unique_otus_histo_bin_end_x[j]).toFixed(0) + ")";
                           this.firstBinName = (this.comparingCohortsPhylumData[0][i].num_unique_otus_histo_bin_start_x[j]).toFixed(0) + "-" + (this.comparingCohortsPhylumData[0][i].num_unique_otus_histo_bin_end_x[j]).toFixed(0);
                       } else if (j == this.comparingCohortsPhylumData[0][i].num_unique_otus_histo_bin_height_y.length - 1) {
                           binName = "[" + (this.comparingCohortsPhylumData[0][i].num_unique_otus_histo_bin_start_x[j]).toFixed(0) + "-" + (this.comparingCohortsPhylumData[0][i].num_unique_otus_histo_bin_end_x[j]).toFixed(0) + "]";
                           this.maxXLabel = (this.comparingCohortsPhylumData[0][i].num_unique_otus_histo_bin_end_x[j]).toFixed(0);
                       } else
                           binName = "[" + (this.comparingCohortsPhylumData[0][i].num_unique_otus_histo_bin_start_x[j]).toFixed(0) + "-" + (this.comparingCohortsPhylumData[0][i].num_unique_otus_histo_bin_end_x[j]).toFixed(0) + ")";
                       data.push({
                           "binName": binName,
                           "barDataRecords": barDataRecords
                       })
                   }
                   if (countablePhylaPartOne.indexOf(this.comparingCohortsPhylumData[0][i].node_name) != -1) {
                       this.richnessesPartOne.push({
                           "phylum": this.comparingCohortsPhylumData[0][i].node_name,
                           "data": data});
                   } else if (countablePhylaPartTwo.indexOf(this.comparingCohortsPhylumData[0][i].node_name) != -1) {
                       this.richnessesPartTwo.push({
                           "phylum": this.comparingCohortsPhylumData[0][i].node_name,
                           "data": data});
                   }
               }
           }
       }
    }
    
    /*mock richness table data used for area chart. This is no longer used after we plug in data from API, but kept to show the input format that is necessary for the density plot
    readRichness(): Richness[] {
        return [
                {"phylum": "firmucutes", "data": 
                
                [
                    {
                        "cohortName": "baseline",
                        "points": [
                            {"xValue": 0,
                             "yValue": 0
                            },
                            {"xValue": 1500,
                             "yValue": 0
                            },
                            {"xValue": 1600,
                             "yValue": 0.9
                            },
                            {"xValue": 1700,
                             "yValue": 0.5
                            },
                            {"xValue": 1750,
                             "yValue": 0.6
                            },
                            {"xValue": 1800,
                             "yValue": 0.65
                            },
                            {"xValue": 1900,
                             "yValue": 0.65
                            },
                            {"xValue": 2000,
                             "yValue": 0.4
                            },
                            {"xValue": 2250,
                             "yValue": 0
                            }
                        ]
                    },
                    {
                        "cohortName": "cohort 1",
                        "points": [
                            {"xValue": 1600,
                             "yValue": 0
                            },
                            {"xValue": 1900,
                             "yValue": 0.2
                            },
                            {"xValue": 2000,
                             "yValue": 0.3
                            },
                            {"xValue": 2250,
                             "yValue": 0.4
                            },
                            {"xValue": 2500,
                             "yValue": 0.5
                            },
                            {"xValue": 2750,
                             "yValue": 0.85
                            },
                            {"xValue": 3000,
                             "yValue": 0.90
                            },
                            {"xValue": 3250,
                             "yValue": 0.5
                            },
                            {"xValue": 3500,
                             "yValue": 0
                            }
                        ]
                    },
                    {
                        "cohortName": "individual",
                        "points": [
                            {"xValue": 2000,
                             "yValue": 0.8
                            }
                        ]
                    }
                ],
                "densityPlotConfigOptions": {"margin":0,  "maxX":4000,  "maxY":1, "width":200, "height":15, "showAxes":false, "showBubble":false}  
                },
                {"phylum": "bacteriodetes", "data": 
                  
                [
                    {
                        "cohortName": "baseline",
                        "points": [
                            {"xValue": 0,
                             "yValue": 0
                            },
                            {"xValue": 1500,
                             "yValue": 0
                            },
                            {"xValue": 1600,
                             "yValue": 0.9
                            },
                            {"xValue": 1700,
                             "yValue": 0.5
                            },
                            {"xValue": 1750,
                             "yValue": 0.6
                            },
                            {"xValue": 1800,
                             "yValue": 0.65
                            },
                            {"xValue": 1900,
                             "yValue": 0.65
                            },
                            {"xValue": 2000,
                             "yValue": 0.4
                            },
                            {"xValue": 2250,
                             "yValue": 0
                            }
                        ]
                    },
                    {
                        "cohortName": "cohort 1",
                        "points": [
                            {"xValue": 1600,
                             "yValue": 0
                            },
                            {"xValue": 1900,
                             "yValue": 0.2
                            },
                            {"xValue": 2000,
                             "yValue": 0.3
                            },
                            {"xValue": 2250,
                             "yValue": 0.4
                            },
                            {"xValue": 2500,
                             "yValue": 0.5
                            },
                            {"xValue": 2750,
                             "yValue": 0.85
                            },
                            {"xValue": 3000,
                             "yValue": 0.90
                            },
                            {"xValue": 3250,
                             "yValue": 0.5
                            },
                            {"xValue": 3500,
                             "yValue": 0
                            }
                        ]
                    },
                    {
                        "cohortName": "individual",
                        "points": [
                            {"xValue": 2000,
                             "yValue": 0.8
                            }
                        ]
                    }
                ],
                "densityPlotConfigOptions": {"margin":0,  "maxX":4000,  "maxY":1, "width":200, "height":15, "showAxes": false, "showBubble": false}    
                },
                {"phylum": "proteobacteria", "data": 
                 
                [
                    {
                        "cohortName": "baseline",
                        "points": [
                            {"xValue": 0,
                             "yValue": 0
                            },
                            {"xValue": 1500,
                             "yValue": 0
                            },
                            {"xValue": 1600,
                             "yValue": 0.9
                            },
                            {"xValue": 1700,
                             "yValue": 0.5
                            },
                            {"xValue": 1750,
                             "yValue": 0.6
                            },
                            {"xValue": 1800,
                             "yValue": 0.65
                            },
                            {"xValue": 1900,
                             "yValue": 0.65
                            },
                            {"xValue": 2000,
                             "yValue": 0.4
                            },
                            {"xValue": 2250,
                             "yValue": 0
                            }
                        ]
                    },
                    {
                        "cohortName": "cohort 1",
                        "points": [
                            {"xValue": 1600,
                             "yValue": 0
                            },
                            {"xValue": 1900,
                             "yValue": 0.2
                            },
                            {"xValue": 2000,
                             "yValue": 0.3
                            },
                            {"xValue": 2250,
                             "yValue": 0.4
                            },
                            {"xValue": 2500,
                             "yValue": 0.5
                            },
                            {"xValue": 2750,
                             "yValue": 0.85
                            },
                            {"xValue": 3000,
                             "yValue": 0.90
                            },
                            {"xValue": 3250,
                             "yValue": 0.5
                            },
                            {"xValue": 3500,
                             "yValue": 0
                            }
                        ]
                    },
                    {
                        "cohortName": "individual",
                        "points": [
                            {"xValue": 2000,
                             "yValue": 0.8
                            }
                        ]
                    }
                ],
                "densityPlotConfigOptions": {"margin":0,  "maxX":4000,  "maxY":1, "width":200, "height":15, "showAxes": false, "showBubble": false}    
                },
                {"phylum": "fibrobacteres", "data": 
                  
                [
                    {
                        "cohortName": "baseline",
                        "points": [
                            {"xValue": 0,
                             "yValue": 0
                            },
                            {"xValue": 1500,
                             "yValue": 0
                            },
                            {"xValue": 1600,
                             "yValue": 0.9
                            },
                            {"xValue": 1700,
                             "yValue": 0.5
                            },
                            {"xValue": 1750,
                             "yValue": 0.6
                            },
                            {"xValue": 1800,
                             "yValue": 0.65
                            },
                            {"xValue": 1900,
                             "yValue": 0.65
                            },
                            {"xValue": 2000,
                             "yValue": 0.4
                            },
                            {"xValue": 2250,
                             "yValue": 0
                            }
                        ]
                    },
                    {
                        "cohortName": "cohort 1",
                        "points": [
                            {"xValue": 1800,
                             "yValue": 0
                            },
                            {"xValue": 1900,
                             "yValue": 0.2
                            },
                            {"xValue": 2000,
                             "yValue": 0.3
                            },
                            {"xValue": 2250,
                             "yValue": 0.4
                            },
                            {"xValue": 2500,
                             "yValue": 0.5
                            },
                            {"xValue": 2750,
                             "yValue": 0.85
                            },
                            {"xValue": 3000,
                             "yValue": 0.90
                            },
                            {"xValue": 3250,
                             "yValue": 0.5
                            },
                            {"xValue": 3500,
                             "yValue": 0
                            }
                        ]
                    },
                    {
                        "cohortName": "individual",
                        "points": [
                            {"xValue": 2000,
                             "yValue": 0.8
                            }
                        ]
                    }
                ],
                "densityPlotConfigOptions": {"margin":0,  "maxX":4000,  "maxY":1, "width":200, "height":15, "showAxes": false, "showBubble": false}
                },
                {"phylum": "fusobaacteria", "data": 
                  
                [
                    {
                        "cohortName": "baseline",
                        "points": [
                            {"xValue": 0,
                             "yValue": 0
                            },
                            {"xValue": 1500,
                             "yValue": 0
                            },
                            {"xValue": 1600,
                             "yValue": 0.9
                            },
                            {"xValue": 1700,
                             "yValue": 0.5
                            },
                            {"xValue": 1750,
                             "yValue": 0.6
                            },
                            {"xValue": 1800,
                             "yValue": 0.65
                            },
                            {"xValue": 1900,
                             "yValue": 0.65
                            },
                            {"xValue": 2000,
                             "yValue": 0.4
                            },
                            {"xValue": 2250,
                             "yValue": 0
                            }
                        ]
                    },
                    {
                        "cohortName": "cohort 1",
                        "points": [
                            {"xValue": 1500,
                             "yValue": 0
                            },
                            {"xValue": 1900,
                             "yValue": 0.2
                            },
                            {"xValue": 2000,
                             "yValue": 0.3
                            },
                            {"xValue": 2250,
                             "yValue": 0.4
                            },
                            {"xValue": 2500,
                             "yValue": 0.5
                            },
                            {"xValue": 2750,
                             "yValue": 0.85
                            },
                            {"xValue": 3000,
                             "yValue": 0.90
                            },
                            {"xValue": 3250,
                             "yValue": 0.5
                            },
                            {"xValue": 3500,
                             "yValue": 0
                            }
                        ]
                    },
                    {
                        "cohortName": "individual",
                        "points": [
                            {"xValue": 2000,
                             "yValue": 0.8
                            }
                        ]
                    }
                ],
                "densityPlotConfigOptions": {"margin":0,  "maxX":4000,  "maxY":1, "width":200, "height":15, "showAxes": false, "showBubble": false}    
                },
                {"phylum": "tenericutes", "data": 
                 
                [
                    {
                        "cohortName": "baseline",
                        "points": [
                            {"xValue": 0,
                             "yValue": 0
                            },
                            {"xValue": 1500,
                             "yValue": 0
                            },
                            {"xValue": 1600,
                             "yValue": 0.9
                            },
                            {"xValue": 1700,
                             "yValue": 0.5
                            },
                            {"xValue": 1750,
                             "yValue": 0.6
                            },
                            {"xValue": 1800,
                             "yValue": 0.65
                            },
                            {"xValue": 1900,
                             "yValue": 0.65
                            },
                            {"xValue": 2000,
                             "yValue": 0.4
                            },
                            {"xValue": 2250,
                             "yValue": 0
                            }
                        ]
                    },
                    {
                        "cohortName": "cohort 1",
                        "points": [
                            {"xValue": 1200,
                             "yValue": 0
                            },
                            {"xValue": 1900,
                             "yValue": 0.2
                            },
                            {"xValue": 2000,
                             "yValue": 0.3
                            },
                            {"xValue": 2250,
                             "yValue": 0.4
                            },
                            {"xValue": 2500,
                             "yValue": 0.5
                            },
                            {"xValue": 2750,
                             "yValue": 0.85
                            },
                            {"xValue": 3000,
                             "yValue": 0.90
                            },
                            {"xValue": 3250,
                             "yValue": 0.5
                            },
                            {"xValue": 3500,
                             "yValue": 0
                            }
                        ]
                    },
                    {
                        "cohortName": "individual",
                        "points": [
                            {"xValue": 2000,
                             "yValue": 0.8
                            }
                        ]
                    }
                ],
                "densityPlotConfigOptions": {"margin":0,  "maxX":4000,  "maxY":1, "width":200, "height":15, "showAxes": false, "showBubble": false}    
                },
                {"phylum": "spirochaetes", "data": 
                 
                [
                    {
                        "cohortName": "baseline",
                        "points": [
                            {"xValue": 0,
                             "yValue": 0
                            },
                            {"xValue": 1500,
                             "yValue": 0
                            },
                            {"xValue": 1600,
                             "yValue": 0.9
                            },
                            {"xValue": 1700,
                             "yValue": 0.5
                            },
                            {"xValue": 1750,
                             "yValue": 0.6
                            },
                            {"xValue": 1800,
                             "yValue": 0.65
                            },
                            {"xValue": 1900,
                             "yValue": 0.65
                            },
                            {"xValue": 2000,
                             "yValue": 0.4
                            },
                            {"xValue": 2250,
                             "yValue": 0
                            }
                        ]
                    },
                    {
                        "cohortName": "cohort 1",
                        "points": [
                            {"xValue": 1800,
                             "yValue": 0
                            },
                            {"xValue": 1900,
                             "yValue": 0.2
                            },
                            {"xValue": 2000,
                             "yValue": 0.3
                            },
                            {"xValue": 2250,
                             "yValue": 0.4
                            },
                            {"xValue": 2500,
                             "yValue": 0.5
                            },
                            {"xValue": 2750,
                             "yValue": 0.85
                            },
                            {"xValue": 3000,
                             "yValue": 0.90
                            },
                            {"xValue": 3250,
                             "yValue": 0.5
                            },
                            {"xValue": 3500,
                             "yValue": 0
                            }
                        ]
                    },
                    {
                        "cohortName": "individual",
                        "points": [
                            {"xValue": 2000,
                             "yValue": 0.8
                            }
                        ]
                    }
                ],
                "densityPlotConfigOptions": {"margin":0,  "maxX":4000,  "maxY":1, "width":200, "height":15, "showAxes": false, "showBubble": false}    
                },
                {"phylum": "verrucomicobia", "data": 
                
                [
                    {
                        "cohortName": "baseline",
                        "points": [
                            {"xValue": 0,
                             "yValue": 0
                            },
                            {"xValue": 1500,
                             "yValue": 0
                            },
                            {"xValue": 1600,
                             "yValue": 0.9
                            },
                            {"xValue": 1700,
                             "yValue": 0.5
                            },
                            {"xValue": 1750,
                             "yValue": 0.6
                            },
                            {"xValue": 1800,
                             "yValue": 0.65
                            },
                            {"xValue": 1900,
                             "yValue": 0.65
                            },
                            {"xValue": 2000,
                             "yValue": 0.4
                            },
                            {"xValue": 2250,
                             "yValue": 0
                            }
                        ]
                    },
                    {
                        "cohortName": "cohort 1",
                        "points": [
                            {"xValue": 1300,
                             "yValue": 0
                            },
                            {"xValue": 1900,
                             "yValue": 0.2
                            },
                            {"xValue": 2000,
                             "yValue": 0.3
                            },
                            {"xValue": 2250,
                             "yValue": 0.4
                            },
                            {"xValue": 2500,
                             "yValue": 0.5
                            },
                            {"xValue": 2750,
                             "yValue": 0.85
                            },
                            {"xValue": 3000,
                             "yValue": 0.90
                            },
                            {"xValue": 3250,
                             "yValue": 0.5
                            },
                            {"xValue": 3500,
                             "yValue": 0
                            }
                        ]
                    },
                    {
                        "cohortName": "individual",
                        "points": [
                            {"xValue": 2000,
                             "yValue": 0.8
                            }
                        ]
                    }
                ],
                "densityPlotConfigOptions": {"margin":0,  "maxX":4000,  "maxY":1, "width":200, "height":15, "showAxes": false, "showBubble": false}   
                }
            ];
    }
    */
}
