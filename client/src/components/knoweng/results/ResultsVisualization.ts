import {Component, OnInit, Input} from '@angular/core';
import {Router, ActivatedRoute, Params} from '@angular/router';

import {JobService} from '../../../services/knoweng/JobService';
import {Job} from '../../../models/knoweng/Job';

import {LogService} from '../../../services/common/LogService';

@Component({
    moduleId: module.id,
    selector: 'results-visualization',
    templateUrl: './ResultsVisualization.html',
    styleUrls: ['./ResultsVisualization.css']
})

export class ResultsVisualization implements OnInit {
    class = 'relative';

    job: Job = null;

    constructor(
        private _jobService: JobService,
        private _router: Router,
        private _route: ActivatedRoute,
        private _logger: LogService) {
    }
    
    ngOnInit() {
        this._route.params
            .subscribe((params : Params) => {
                let jobId = params['id'];
                this.getJob(jobId);
        });
    }
    
    getJob(jobId : string) {
        this._jobService.getJob(jobId)
            .subscribe(
                (job: Job) => {
                    if (job === undefined) {
                        // no match yet; continue waiting
                    } else if (job !== null && this.job !== null && job._id === this.job._id) {
                        // no change; don't reset this.job, or the visualization will reset
                    } else {
                        this.job = job;
                    }
                },
                (error: any) => {
                    if (error.status == 404) {
                        alert(`Job not found.`);
                        this._router.navigate( ['/results'] );
                        this._logger.error("Job not found: " + jobId, error.stack);
                    } else {
                        alert(`Server error. Try again later`);
                        this._logger.error(error.message, error.stack);
                    }
                });
    }
}
