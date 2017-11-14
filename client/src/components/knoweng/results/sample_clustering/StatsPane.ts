import {Component, OnInit, Input} from '@angular/core';

import {Result} from '../../../../models/knoweng/results/SampleClustering';

@Component({
    moduleId: module.id,
    selector: 'stats-pane',
    templateUrl: './StatsPane.html',
    styleUrls: ['./StatsPane.css']
})

export class StatsPane implements OnInit {
    class = 'relative';

    @Input()
    result: Result;

    constructor() {
    }
    ngOnInit() {
    }
}
