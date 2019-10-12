import {Component, OnInit, Input} from '@angular/core';

import {Job} from '../../../../models/knoweng/Job';
import {SignatureScores} from '../../../../models/knoweng/results/SignatureAnalysis';

@Component({
    moduleId: module.id,
    selector: 'sa-data-area',
    templateUrl: './DataArea.html',
    styleUrls: ['./DataArea.css']
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
    scores: SignatureScores;

    @Input()
    currentNumTopSamples: number;

    @Input()
    selectedSignatures: string[];

    /** one of heatmap, network, spreadsheet, job */
    activeTab: string = 'heatmap';

    constructor() {
    }
    ngOnInit() {
    }
}
