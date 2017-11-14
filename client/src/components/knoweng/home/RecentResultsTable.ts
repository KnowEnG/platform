import {Component, OnInit, OnDestroy} from '@angular/core';
import {Router} from '@angular/router';
import {Subscription} from 'rxjs/Subscription';

import {JobService} from '../../../services/knoweng/JobService';
import {Job} from '../../../models/knoweng/Job';

import {LogService} from '../../../services/common/LogService';
import {SessionService} from '../../../services/common/SessionService';

@Component({
    moduleId: module.id,
    selector: 'recent-results-table',
    templateUrl: './RecentResultsTable.html',
    styleUrls: ['./RecentResultsTable.css']
})

export class RecentResultsTable implements OnInit, OnDestroy {
    class = 'relative';

    jobs: Job[] = [];

    sortColumn: string = "start";
    sortReverse: boolean = false;
    showContextMenu: boolean = false;
    contextMenuBottom: number = null;
    contextMenuRight: number = null;
    selectedRowIndex: number = null;
    selectedJob: Job = null;
    hasDownloadInProgress: boolean = false;
    maxLength: number = 15;
    subscription: Subscription;

    constructor(
       private _router: Router,
       private _jobService: JobService,
       private _sessionService: SessionService,
       private _logger: LogService) {
    }
    ngOnInit() {
        // Figure out the Date 1 week ago
        let oneWeekAgo = new Date();
        oneWeekAgo.setDate(oneWeekAgo.getDate() - 7);
        
        this.subscription = this._jobService.getJobs()
            .subscribe(
                (jobs: Array<Job>) => {
                    // sort jobs by date
                    this.jobs = jobs.slice()
                        .filter((a: Job) => oneWeekAgo.getTime() < a.getCreatedDate().getTime())
                        .sort((a: Job, b: Job) => d3.descending(a.getCreatedDate().getTime(), b.getCreatedDate().getTime()));
                },
                (error: any) => {
                    if (error.status == 401) {
                        this._sessionService.redirectToLogin();
                    } else {
                        alert(`Server error. Try again later`);
                        this._logger.error(error.message, error.stack);
                    }
                });
    }
    ngOnDestroy() {
        // prevent memory leak when component destroyed
        this.subscription.unsubscribe();
    }
    sort(column: string) {
        if (column == this.sortColumn) {
            this.sortReverse = !this.sortReverse;
            this._logger.debug("reverse");
        } else {
            this.sortReverse = false;
            this.sortColumn = column;
            this._logger.debug("resort");
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
    openContextMenu(event: Event, index: number) {
        if (!this.hasDownloadInProgress) {
            this.showContextMenu = true;
            this.contextMenuBottom = window.innerHeight - (<any>event).clientY - 85; // 85 looks good on the screen; no science to it
            if (this.contextMenuBottom < 0) {
                this.contextMenuBottom = 0;
            }
            this.contextMenuRight = window.innerWidth - (<any>event).clientX - 15; // 15px is the padding on .context-menu-container
            this.selectedRowIndex = index;
            this.selectedJob = this.jobs[index];
        }
    }
    closeContextMenu(close: boolean) {
        if (close) {
            this.showContextMenu = false;
            this.selectedRowIndex = null;
            this.selectedJob = null;
            this.hasDownloadInProgress = false;
        } else {
            this.hasDownloadInProgress = true;
        }
    }
    
    closePopupMenu() {
        if (!this.hasDownloadInProgress) {
            this.showContextMenu = false;
            this.selectedRowIndex = null;
            this.selectedJob = null;
        }
    }
    
    /* Navigate to ResultVisualization on double-click */
    viewResult(index: number) {
        let job = this.jobs[index];
        
        // Only navigate for completed jobs
        if (job.status === 'completed') {
            this._router.navigate(["/results/" + job._id]);
        }
    }
}
