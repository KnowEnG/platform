import {Component, Input, OnDestroy, OnInit} from '@angular/core';
import {Router} from '@angular/router';
import {Subscription} from 'rxjs/Subscription';

import {Job} from '../../../../models/knoweng/Job';
import {SessionService} from '../../../../services/common/SessionService';
import {LogService} from '../../../../services/common/LogService';
import {SSVState, Spreadsheet, EndJobRequest, SSVStateRequest} from '../../../../models/knoweng/results/SpreadsheetVisualization';
import {SpreadsheetVisualizationService} from '../../../../services/knoweng/SpreadsheetVisualizationService';

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
    
    ssvSub: Subscription;
    
    state: SSVState;
    
    constructor(
        private _ssvService: SpreadsheetVisualizationService,
        private _sessionService: SessionService,
        private _logger: LogService) {
    }
    
    ngOnInit() {
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
        let endJobRequest: EndJobRequest = new EndJobRequest(this.job._id);
        let stateRequest: SSVStateRequest = new SSVStateRequest(null, null, [], [], null, null, null, [], endJobRequest);
        this._ssvService.updateSSVState(stateRequest)
        this.ssvSub.unsubscribe();
    }
}