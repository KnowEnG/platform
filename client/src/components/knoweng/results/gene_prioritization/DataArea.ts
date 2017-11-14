import {Component, OnInit, Input} from '@angular/core';

import {Job} from '../../../../models/knoweng/Job';
import {ResponseScores} from '../../../../models/knoweng/results/GenePrioritization';

//import {Clustergram} from './Clustergram';

@Component({
    moduleId: module.id,
    selector: 'gp-data-area',
    templateUrl: './DataArea.html',
    styleUrls: ['./DataArea.css']
    //directives: [Clustergram]
})

export class DataArea implements OnInit {
    class = 'relative';

    @Input()
    job: Job;

    @Input()
    gradientMaxColor: string;

    @Input()
    gradientMinColor: string;

    @Input()
    gradientMaxValue: number;

    @Input()
    gradientMinValue: number;

    @Input()
    scores: ResponseScores;

    @Input()
    currentNumTopGenes: number;

    @Input()
    selectedResponses: string[];

    @Input()
    geneIdToNameMap: d3.Map<string>;

    /** one of heatmap, network, spreadsheet, job */
    activeTab: string = 'heatmap';

    constructor() {
    }
    ngOnInit() {
    }
}
