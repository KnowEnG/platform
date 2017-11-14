import {Component, OnInit, Input} from '@angular/core';

import {Result} from '../../../../models/knoweng/results/SampleClustering';
import {Job} from '../../../../models/knoweng/Job';

@Component({
    moduleId: module.id,
    selector: 'sc-data-area',
    templateUrl: './DataArea.html',
    styleUrls: ['./DataArea.css']
})

export class DataArea implements OnInit {
    class = 'relative';

    @Input()
    job: Job;

    @Input()
    result: Result;

    /** one of visualizations, spreadsheet, job */
    activeTab: string = 'visualizations';

    constructor() {
    }
    ngOnInit() {
    }
}
