import {Component, OnChanges, SimpleChange, Input, EventEmitter, Output} from '@angular/core';
import { Router, ActivatedRoute } from '@angular/router';

import {Job} from '../../../models/knoweng/Job';
import {LogService} from '../../../services/common/LogService';

@Component({
    moduleId: module.id,
    selector: 'results-table-body',
    templateUrl: './ResultsTableBody.html',
    styleUrls: ['./ResultsTableBody.css']
})

export class ResultsTableBody implements OnChanges {
    class = 'relative';

    @Input()
    jobs: Job[];

    @Output()
    jobSelected: EventEmitter<Job> = new EventEmitter<Job>();

    sortColumn: string = "start";
    sortReverse: boolean = false;
    selectedRowIndex: number = null;

    constructor(private logger: LogService, private router: Router, private route: ActivatedRoute) {
    }
    ngOnChanges(changes: {[propertyName: string]: SimpleChange}) {
        // jobs[] may change if a job was deleted; if so, make sure we
        // update our selected job
        if (this.selectedRowIndex !== null) {
            if (this.jobs !== null && this.jobs.length > 0) {
                if (this.selectedRowIndex >= this.jobs.length) {
                    this.selectedRowIndex = this.jobs.length-1;
                }
                this.jobSelected.emit(this.jobs[this.selectedRowIndex]);
            } else {
                this.jobSelected.emit(null);
            }
        }
    }
    sort(column: string) {
        if (column == this.sortColumn) {
            this.sortReverse = !this.sortReverse;
            this.logger.debug("reverse");
        } else {
            this.sortReverse = false;
            this.sortColumn = column;
            this.logger.debug("resort");
        }
        
        if (column === 'status') {
            this.jobs = this.jobs.sort((a: Job, b: Job) => this.sortReverse ? 
                d3.ascending(a.status.toLowerCase(), b.status.toLowerCase())
                    : d3.descending(a.status.toLowerCase(), b.status.toLowerCase()));
        } else if (column === 'pipeline') {
            this.jobs = this.jobs.sort((a: Job, b: Job) => this.sortReverse ? 
                d3.ascending(a.pipeline+a.parameters.method, b.pipeline+b.parameters.method) 
                    : d3.descending(a.pipeline+a.parameters.method, b.pipeline+b.parameters.method));
        } else if (column === 'name') {
            this.jobs = this.jobs.sort((a: Job, b: Job) => this.sortReverse ? 
                d3.ascending(a.name.toLowerCase(), b.name.toLowerCase())
                    : d3.descending(a.name.toLowerCase(), b.name.toLowerCase()));
        } else if (column === 'start') {
            this.jobs = this.jobs.sort((a: Job, b: Job) => this.sortReverse ? 
                d3.ascending(a.getCreatedDate().getTime(), b.getCreatedDate().getTime())
                    : d3.descending(a.getCreatedDate().getTime(), b.getCreatedDate().getTime()));
        }
    }
    selectRow(index: number) {
        this.selectedRowIndex = index;
        this.jobSelected.emit(this.jobs[index]);
    }
    
    /* Navigate to ResultVisualization on double-click */
    viewResult(index: number) {
        let job = this.jobs[index];
        
        // Only navigate for completed jobs
        if (job.status === 'completed') {
            this.router.navigate(["./" + job._id], {relativeTo: this.route});
        }
    }

    /* trackByFunction implementation for the list of jobs */
    jobTracker(index: number, item: Job): number {
        return item._id;
    }
}
