import {Component, OnInit, EventEmitter, Output} from '@angular/core';

import {Job} from '../../../models/knoweng/Job';
import {NestFile} from '../../../models/knoweng/NestFile';

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
    
    @Output()
    fileSelected: EventEmitter<NestFile> = new EventEmitter<NestFile>();
    

    constructor() {
    }
    ngOnInit() {
    }
}
