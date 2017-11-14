import {Component, OnInit, OnDestroy, Input} from '@angular/core';
import {Router} from '@angular/router';
import {Subscription} from 'rxjs/Subscription';

import {Job} from '../../../../models/knoweng/Job';
import {Result} from '../../../../models/knoweng/results/SampleClustering';
import {SpreadsheetVisualizationService} from '../../../../services/knoweng/SpreadsheetVisualizationService';
import {SessionService} from '../../../../services/common/SessionService';
import {LogService} from '../../../../services/common/LogService';

@Component({
    moduleId: module.id,
    selector: 'ss-visualization',
    templateUrl: './SSVisualization.html',
    styleUrls: ['./SSVisualization.css']
})

export class SSVisualization implements OnInit, OnDestroy {
    class = 'relative';

    @Input()
    job: Job;

    result: Result;
    ssSub: Subscription;

    constructor(
        private _ssService: SpreadsheetVisualizationService,
        private _router: Router,
        private _sessionService: SessionService,
        private _logger: LogService) {
    }
    ngOnInit() {
        this.ssSub = this._ssService.getResult(this.job._id)
            .subscribe(
                (result: Result) => {
                    this.result = result;
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
        this.ssSub.unsubscribe();
    }
}
