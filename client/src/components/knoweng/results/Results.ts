import {Component, ChangeDetectorRef, OnInit, OnDestroy} from '@angular/core';
import {Router, NavigationEnd} from "@angular/router";

import {GoogleAnalyticsService} from '../../../services/common/GoogleAnalyticsService';

import {Job} from '../../../models/knoweng/Job';
import {NestFile} from '../../../models/knoweng/NestFile';

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
    /**
     * In browsing mode, this is the file the user has selected from the list of
     * files. Its details will be loaded to a panel on the right.
     */
    selectedFile: NestFile = null;
    
    constructor(private _changeDetector: ChangeDetectorRef,
                private _router: Router, 
                private _googleAnalytics: GoogleAnalyticsService) {
        this._router.events.subscribe(event => {
          if (event instanceof NavigationEnd) {
            this._googleAnalytics.emitPageView(event.urlAfterRedirects);
          }
        });
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
        this.selectedFile = null;
        this.selectedJob = job;
        this._changeDetector.detectChanges();
    }
    onJobOpened(job: Job): void {
        this.visualizationId = job._id;
        this._changeDetector.detectChanges();
    }
    
    onFileSelected(file: NestFile): void {
        this.selectedJob = null;
        this.selectedFile = file;
    }
}
