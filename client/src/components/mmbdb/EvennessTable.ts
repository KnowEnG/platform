import {Component, OnInit, Input} from '@angular/core';
import {AreaChart, CohortDataRecord} from "./AreaChart";
import {CohortPhylumData} from '../../models/mmbdb/CohortComparison';
import {GroupedBarChart, GroupedBarChartDataRecord, BarDataRecord} from './GroupedBarChart';

export interface Evenness {
    phylum: string;
    data: GroupedBarChartDataRecord[];
}

@Component ({
    moduleId: module.id,
    selector: 'evenness-table',
    templateUrl: './EvennessTable.html',
    styleUrls: ['./RichnessEvennessTable.css']
})

export class EvennessTable implements OnInit{
    class = 'relative';
    
    evennessesPartOne: Evenness[] = [];
    
    evennessesPartTwo: Evenness[] = [];
    
    firstBinName: string = '';
    
    maxXLabel: string = '';
    
    @Input()
    comparingCohortsPhylumData: Array<CohortPhylumData[]>;
    
    ngOnInit() {
       this.prepareEvennessData();
    }
    
    prepareEvennessData() {
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
                       "sampleSize": this.comparingCohortsPhylumData[0][i].normalized_entropy_histo_num_zeros
                   });
                   barDataRecordsAtZero.push({
                       "cohort": "Cohort 1",
                       "sampleSize": this.comparingCohortsPhylumData[1][i].normalized_entropy_histo_num_zeros
                   });
                   barDataRecordsAtZero.push({
                       "cohort": "Individual",
                       "sampleSize": this.comparingCohortsPhylumData[2][i].normalized_entropy_histo_num_zeros
                   });
                   data.push({
                       "binName": "0",
                       "barDataRecords": barDataRecordsAtZero
                   });
                   for (var j = 0; j < this.comparingCohortsPhylumData[0][i].normalized_entropy_histo_bin_height_y.length; j++) {
                       var barDataRecords: BarDataRecord[] = [];
                       barDataRecords.push({
                           "cohort": "Baseline",
                           "sampleSize": this.comparingCohortsPhylumData[0][i].normalized_entropy_histo_bin_height_y[j]
                       });
                       barDataRecords.push({
                           "cohort": "Cohort 1",
                           "sampleSize": this.comparingCohortsPhylumData[1][i].normalized_entropy_histo_bin_height_y[j]
                       });
                       barDataRecords.push({
                           "cohort": "Individual",
                           "sampleSize": this.comparingCohortsPhylumData[2][i].normalized_entropy_histo_bin_height_y[j]
                       })
                       var binName: string = '';
                       if (j == 0) {
                           binName = "(" + (this.comparingCohortsPhylumData[0][i].normalized_entropy_histo_bin_start_x[j]).toFixed(2) + "-" + (this.comparingCohortsPhylumData[0][i].normalized_entropy_histo_bin_end_x[j]).toFixed(2) + ")";
                           this.firstBinName = (this.comparingCohortsPhylumData[0][i].normalized_entropy_histo_bin_start_x[j]).toFixed(2) + "-" + (this.comparingCohortsPhylumData[0][i].normalized_entropy_histo_bin_end_x[j]).toFixed(2);
                       } else if (j == this.comparingCohortsPhylumData[0][i].normalized_entropy_histo_bin_height_y.length - 1) {
                           binName = "[" + (this.comparingCohortsPhylumData[0][i].normalized_entropy_histo_bin_start_x[j]).toFixed(2) + "-" + (this.comparingCohortsPhylumData[0][i].normalized_entropy_histo_bin_end_x[j]).toFixed(2) + "]";
                           this.maxXLabel = this.comparingCohortsPhylumData[0][i].normalized_entropy_histo_bin_end_x[j].toFixed(2);
                       } else
                           binName = "[" + (this.comparingCohortsPhylumData[0][i].normalized_entropy_histo_bin_start_x[j]).toFixed(2) + "-" + (this.comparingCohortsPhylumData[0][i].normalized_entropy_histo_bin_end_x[j]).toFixed(2) + ")";
                       data.push({
                           "binName": binName,
                           "barDataRecords": barDataRecords
                       })
                   }
                   if (countablePhylaPartOne.indexOf(this.comparingCohortsPhylumData[0][i].node_name) != -1) {
                       this.evennessesPartOne.push({
                           "phylum": this.comparingCohortsPhylumData[0][i].node_name,
                           "data": data
                       });
                   } else if (countablePhylaPartTwo.indexOf(this.comparingCohortsPhylumData[0][i].node_name) != -1) {
                       this.evennessesPartTwo.push({
                            "phylum": this.comparingCohortsPhylumData[0][i].node_name,
                            "data": data
                       });
                   }
               }
           }
       }
    }
    
    /*readEvenness(): Evenness[] {
         return [
                {"phylum": "firmucutes", "data": [
                    {
                        "cohortName": "baseline",
                        "points": [
                            {"xValue": 0,
                             "yValue": 0
                            },
                            {"xValue": 20,
                             "yValue": 0
                            },
                            {"xValue": 21,
                             "yValue": 0.9
                            },
                            {"xValue": 22,
                             "yValue": 0.5
                            },
                            {"xValue": 23,
                             "yValue": 0.6
                            },
                            {"xValue": 24,
                             "yValue": 0.65
                            },
                            {"xValue": 25,
                             "yValue": 0.65
                            },
                            {"xValue": 26,
                             "yValue": 0.4
                            },
                            {"xValue": 27,
                             "yValue": 0
                            }
                        ]
                    },
                    {
                        "cohortName": "cohort 1",
                        "points": [
                            {"xValue": 12,
                             "yValue": 0
                            },
                            {"xValue": 25,
                             "yValue": 0.2
                            },
                            {"xValue": 26,
                             "yValue": 0.3
                            },
                            {"xValue": 27,
                             "yValue": 0.4
                            },
                            {"xValue": 28,
                             "yValue": 0.5
                            },
                            {"xValue": 29,
                             "yValue": 0.85
                            },
                            {"xValue": 30,
                             "yValue": 0.90
                            },
                            {"xValue": 31,
                             "yValue": 0.5
                            },
                            {"xValue": 32,
                             "yValue": 0
                            }
                        ]
                    },
                    {
                        "cohortName": "individual",
                        "points": [
                            {"xValue": 26,
                             "yValue": 0.8
                            }
                        ]
                    }
                ]},
                {"phylum": "bacteriodetes", "data": [
                    {
                        "cohortName": "baseline",
                        "points": [
                            {"xValue": 0,
                             "yValue": 0
                            },
                            {"xValue": 20,
                             "yValue": 0
                            },
                            {"xValue": 21,
                             "yValue": 0.9
                            },
                            {"xValue": 22,
                             "yValue": 0.5
                            },
                            {"xValue": 23,
                             "yValue": 0.6
                            },
                            {"xValue": 24,
                             "yValue": 0.65
                            },
                            {"xValue": 25,
                             "yValue": 0.65
                            },
                            {"xValue": 26,
                             "yValue": 0.4
                            },
                            {"xValue": 27,
                             "yValue": 0
                            }
                        ]
                    },
                    {
                        "cohortName": "cohort 1",
                        "points": [
                            {"xValue": 13,
                             "yValue": 0
                            },
                            {"xValue": 25,
                             "yValue": 0.2
                            },
                            {"xValue": 26,
                             "yValue": 0.3
                            },
                            {"xValue": 27,
                             "yValue": 0.4
                            },
                            {"xValue": 28,
                             "yValue": 0.5
                            },
                            {"xValue": 29,
                             "yValue": 0.85
                            },
                            {"xValue": 30,
                             "yValue": 0.90
                            },
                            {"xValue": 31,
                             "yValue": 0.5
                            },
                            {"xValue": 32,
                             "yValue": 0
                            }
                        ]
                    },
                    {
                        "cohortName": "individual",
                        "points": [
                            {"xValue": 26,
                             "yValue": 0.8
                            }
                        ]
                    }
                ]},
                {"phylum": "proteobacteria", "data": [
                    {
                        "cohortName": "baseline",
                        "points": [
                            {"xValue": 0,
                             "yValue": 0
                            },
                            {"xValue": 20,
                             "yValue": 0
                            },
                            {"xValue": 21,
                             "yValue": 0.9
                            },
                            {"xValue": 22,
                             "yValue": 0.5
                            },
                            {"xValue": 23,
                             "yValue": 0.6
                            },
                            {"xValue": 24,
                             "yValue": 0.65
                            },
                            {"xValue": 25,
                             "yValue": 0.65
                            },
                            {"xValue": 26,
                             "yValue": 0.4
                            },
                            {"xValue": 27,
                             "yValue": 0
                            }
                        ]
                    },
                    {
                        "cohortName": "cohort 1",
                        "points": [
                            {"xValue": 14,
                             "yValue": 0
                            },
                            {"xValue": 25,
                             "yValue": 0.2
                            },
                            {"xValue": 26,
                             "yValue": 0.3
                            },
                            {"xValue": 27,
                             "yValue": 0.4
                            },
                            {"xValue": 28,
                             "yValue": 0.5
                            },
                            {"xValue": 29,
                             "yValue": 0.85
                            },
                            {"xValue": 30,
                             "yValue": 0.90
                            },
                            {"xValue": 31,
                             "yValue": 0.5
                            },
                            {"xValue": 32,
                             "yValue": 0
                            }
                        ]
                    },
                    {
                        "cohortName": "individual",
                        "points": [
                            {"xValue": 26,
                             "yValue": 0.8
                            }
                        ]
                    }
                ]},
                {"phylum": "fibrobacteres", "data": [
                    {
                        "cohortName": "baseline",
                        "points": [
                            {"xValue": 0,
                             "yValue": 0
                            },
                            {"xValue": 20,
                             "yValue": 0
                            },
                            {"xValue": 21,
                             "yValue": 0.9
                            },
                            {"xValue": 22,
                             "yValue": 0.5
                            },
                            {"xValue": 23,
                             "yValue": 0.6
                            },
                            {"xValue": 24,
                             "yValue": 0.65
                            },
                            {"xValue": 25,
                             "yValue": 0.65
                            },
                            {"xValue": 26,
                             "yValue": 0.4
                            },
                            {"xValue": 27,
                             "yValue": 0
                            }
                        ]
                    },
                    {
                        "cohortName": "cohort 1",
                        "points": [
                            {"xValue": 15,
                             "yValue": 0
                            },
                            {"xValue": 25,
                             "yValue": 0.2
                            },
                            {"xValue": 26,
                             "yValue": 0.3
                            },
                            {"xValue": 27,
                             "yValue": 0.4
                            },
                            {"xValue": 28,
                             "yValue": 0.5
                            },
                            {"xValue": 29,
                             "yValue": 0.85
                            },
                            {"xValue": 30,
                             "yValue": 0.90
                            },
                            {"xValue": 31,
                             "yValue": 0.5
                            },
                            {"xValue": 32,
                             "yValue": 0
                            }
                        ]
                    },
                    {
                        "cohortName": "individual",
                        "points": [
                            {"xValue": 26,
                             "yValue": 0.8
                            }
                        ]
                    }
                ]},
                {"phylum": "fusobaacteria", "data": [
                    {
                        "cohortName": "baseline",
                        "points": [
                            {"xValue": 0,
                             "yValue": 0
                            },
                            {"xValue": 20,
                             "yValue": 0
                            },
                            {"xValue": 21,
                             "yValue": 0.9
                            },
                            {"xValue": 22,
                             "yValue": 0.5
                            },
                            {"xValue": 23,
                             "yValue": 0.6
                            },
                            {"xValue": 24,
                             "yValue": 0.65
                            },
                            {"xValue": 25,
                             "yValue": 0.65
                            },
                            {"xValue": 26,
                             "yValue": 0.4
                            },
                            {"xValue": 27,
                             "yValue": 0
                            }
                        ]
                    },
                    {
                        "cohortName": "cohort 1",
                        "points": [
                            {"xValue": 16,
                             "yValue": 0
                            },
                            {"xValue": 25,
                             "yValue": 0.2
                            },
                            {"xValue": 26,
                             "yValue": 0.3
                            },
                            {"xValue": 27,
                             "yValue": 0.4
                            },
                            {"xValue": 28,
                             "yValue": 0.5
                            },
                            {"xValue": 29,
                             "yValue": 0.85
                            },
                            {"xValue": 30,
                             "yValue": 0.90
                            },
                            {"xValue": 31,
                             "yValue": 0.5
                            },
                            {"xValue": 32,
                             "yValue": 0
                            }
                        ]
                    },
                    {
                        "cohortName": "individual",
                        "points": [
                            {"xValue": 26,
                             "yValue": 0.8
                            }
                        ]
                    }
                ]},
                {"phylum": "tenericutes", "data": [
                    {
                        "cohortName": "baseline",
                        "points": [
                            {"xValue": 0,
                             "yValue": 0
                            },
                            {"xValue": 20,
                             "yValue": 0
                            },
                            {"xValue": 21,
                             "yValue": 0.9
                            },
                            {"xValue": 22,
                             "yValue": 0.5
                            },
                            {"xValue": 23,
                             "yValue": 0.6
                            },
                            {"xValue": 24,
                             "yValue": 0.65
                            },
                            {"xValue": 25,
                             "yValue": 0.65
                            },
                            {"xValue": 26,
                             "yValue": 0.4
                            },
                            {"xValue": 27,
                             "yValue": 0
                            }
                        ]
                    },
                    {
                        "cohortName": "cohort 1",
                        "points": [
                            {"xValue": 17,
                             "yValue": 0
                            },
                            {"xValue": 25,
                             "yValue": 0.2
                            },
                            {"xValue": 26,
                             "yValue": 0.3
                            },
                            {"xValue": 27,
                             "yValue": 0.4
                            },
                            {"xValue": 28,
                             "yValue": 0.5
                            },
                            {"xValue": 29,
                             "yValue": 0.85
                            },
                            {"xValue": 30,
                             "yValue": 0.90
                            },
                            {"xValue": 31,
                             "yValue": 0.5
                            },
                            {"xValue": 32,
                             "yValue": 0
                            }
                        ]
                    },
                    {
                        "cohortName": "individual",
                        "points": [
                            {"xValue": 26,
                             "yValue": 0.8
                            }
                        ]
                    }
                ]},
                {"phylum": "spirochaetes", "data": [
                    {
                        "cohortName": "baseline",
                        "points": [
                            {"xValue": 0,
                             "yValue": 0
                            },
                            {"xValue": 20,
                             "yValue": 0
                            },
                            {"xValue": 21,
                             "yValue": 0.9
                            },
                            {"xValue": 22,
                             "yValue": 0.5
                            },
                            {"xValue": 23,
                             "yValue": 0.6
                            },
                            {"xValue": 24,
                             "yValue": 0.65
                            },
                            {"xValue": 25,
                             "yValue": 0.65
                            },
                            {"xValue": 26,
                             "yValue": 0.4
                            },
                            {"xValue": 27,
                             "yValue": 0
                            }
                        ]
                    },
                    {
                        "cohortName": "cohort 1",
                        "points": [
                            {"xValue": 18,
                             "yValue": 0
                            },
                            {"xValue": 25,
                             "yValue": 0.2
                            },
                            {"xValue": 26,
                             "yValue": 0.3
                            },
                            {"xValue": 27,
                             "yValue": 0.4
                            },
                            {"xValue": 28,
                             "yValue": 0.5
                            },
                            {"xValue": 29,
                             "yValue": 0.85
                            },
                            {"xValue": 30,
                             "yValue": 0.90
                            },
                            {"xValue": 31,
                             "yValue": 0.5
                            },
                            {"xValue": 32,
                             "yValue": 0
                            }
                        ]
                    },
                    {
                        "cohortName": "individual",
                        "points": [
                            {"xValue": 26,
                             "yValue": 0.8
                            }
                        ]
                    }
                ]},
                {"phylum": "verrucomicobia", "data": [
                    {
                        "cohortName": "baseline",
                        "points": [
                            {"xValue": 0,
                             "yValue": 0
                            },
                            {"xValue": 20,
                             "yValue": 0
                            },
                            {"xValue": 21,
                             "yValue": 0.9
                            },
                            {"xValue": 22,
                             "yValue": 0.5
                            },
                            {"xValue": 23,
                             "yValue": 0.6
                            },
                            {"xValue": 24,
                             "yValue": 0.65
                            },
                            {"xValue": 25,
                             "yValue": 0.65
                            },
                            {"xValue": 26,
                             "yValue": 0.4
                            },
                            {"xValue": 27,
                             "yValue": 0
                            }
                        ]
                    },
                    {
                        "cohortName": "cohort 1",
                        "points": [
                            {"xValue": 19,
                             "yValue": 0
                            },
                            {"xValue": 25,
                             "yValue": 0.2
                            },
                            {"xValue": 26,
                             "yValue": 0.3
                            },
                            {"xValue": 27,
                             "yValue": 0.4
                            },
                            {"xValue": 28,
                             "yValue": 0.5
                            },
                            {"xValue": 29,
                             "yValue": 0.85
                            },
                            {"xValue": 30,
                             "yValue": 0.90
                            },
                            {"xValue": 31,
                             "yValue": 0.5
                            },
                            {"xValue": 32,
                             "yValue": 0
                            }
                        ]
                    },
                    {
                        "cohortName": "individual",
                        "points": [
                            {"xValue": 26,
                             "yValue": 0.8
                            }
                        ]
                    }
                ]}
            ];
    }*/
}
    

