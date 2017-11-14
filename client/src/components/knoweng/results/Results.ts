import {Component, ChangeDetectorRef, OnInit, OnDestroy} from '@angular/core';

import {Job} from '../../../models/knoweng/Job';

@Component({
    moduleId: module.id,
    selector: 'results',
    templateUrl: './Results.html',
    styleUrls: ['./Results.css']
})

export class Results implements OnInit, OnDestroy {
    class = 'relative';
    /**
     * In browsing mode, this is the job the user has selected from the list of
     * jobs. Its details will be loaded to a panel on the right.
     */
    selectedJob: Job = null;
    /**
     * In visualization mode, this is the id of the job whose results are to be
     * visualized.
     */
    visualizationId: number = null;
    constructor(private _changeDetector: ChangeDetectorRef) {
    }
    ngOnInit() {
        // this.visualizationId = this._routeParams.get('id'); TODO wait for new router
        // TODO consider using visualizationJob instead of visualizationId; with
        // routing, that'd probably mean moving the jobService here and passing
        // the jobs array down to the table
        // or with new router, is it possible to assign one component when param
        // present and another route when param absent?
    }
    ngOnDestroy() {
    }
    onJobSelected(job: Job): void {
        this.selectedJob = job;
        this._changeDetector.detectChanges();
    }
    onJobOpened(job: Job): void {
        this.visualizationId = job._id;
        this._changeDetector.detectChanges();
    }
}
