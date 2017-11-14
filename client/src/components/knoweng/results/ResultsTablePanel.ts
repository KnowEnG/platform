import {Component, OnInit, EventEmitter, Output} from '@angular/core';

import {Job} from '../../../models/knoweng/Job';

@Component({
    moduleId: module.id,
    selector: 'results-table-panel',
    templateUrl: './ResultsTablePanel.html',
    styleUrls: ['./ResultsTablePanel.css']
})

export class ResultsTablePanel implements OnInit {
    class = 'relative';

    @Output()
    jobSelected: EventEmitter<Job> = new EventEmitter<Job>();

    constructor() {
    }
    ngOnInit() {
    }
}
