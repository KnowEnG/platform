import {Component, OnInit, OnDestroy, Input} from '@angular/core';
import {Router} from '@angular/router';
import {Subscription} from 'rxjs/Subscription';

import {Job} from '../../../../models/knoweng/Job';
import {Result} from '../../../../models/knoweng/results/SampleClustering';
import {SSVState, Spreadsheet, EndJobRequest, SSVStateRequest} from '../../../../models/knoweng/results/SpreadsheetVisualization';

import {SampleClusteringService} from '../../../../services/knoweng/SampleClusteringService';
import {SpreadsheetVisualizationService} from '../../../../services/knoweng/SpreadsheetVisualizationService';

import {SessionService} from '../../../../services/common/SessionService';
import {LogService} from '../../../../services/common/LogService';

@Component({
    moduleId: module.id,
    selector: 'sc-visualization',
    templateUrl: './SCVisualization.html',
    styleUrls: ['./SCVisualization.css']
})

export class SCVisualization implements OnInit, OnDestroy {
    class = 'relative';

    @Input()
    job: Job;

    result: Result;
    state: SSVState;

    scSub: Subscription;
    ssvSub: Subscription;

    constructor(
        private _scService: SampleClusteringService,
        private _ssvService: SpreadsheetVisualizationService,
        private _router: Router,
        private _sessionService: SessionService,
        private _logger: LogService) {
    }
    ngOnInit() {
        this.scSub = this._scService.getResult(this.job._id)
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
        this.ssvSub = this._ssvService.getInitialSSVStateWithoutData(this.job._id)
            .subscribe(
                (state: SSVState) => {
                    if (state != null) {
                        this.state = state;
                    }
                },
                (error: any) => {
                    if (error.status == 401) {
                        this._sessionService.redirectToLogin();
                    } else {
                        alert(`Server error. Try again later`);
                        this._logger.error(error.message, error.stack);
                    }
                }
        );
    }
    ngOnDestroy() {
        this.scSub.unsubscribe();
        let endJobRequest: EndJobRequest = new EndJobRequest(this.job._id);
        let stateRequest: SSVStateRequest = new SSVStateRequest(null, null, [], [], null, null, null, [], endJobRequest);
        this._ssvService.updateSSVState(stateRequest)
        this.ssvSub.unsubscribe();
    }
}
