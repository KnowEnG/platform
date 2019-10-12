import {Component, OnInit, OnDestroy, Input} from '@angular/core';
import {Router} from '@angular/router';
import {Subscription} from 'rxjs/Subscription';

import {Job} from '../../../../models/knoweng/Job';
import {SampleScores, SignatureScores, Result} from '../../../../models/knoweng/results/SignatureAnalysis';
import {SignatureAnalysisService} from '../../../../services/knoweng/SignatureAnalysisService';
import {SessionService} from '../../../../services/common/SessionService';
import {LogService} from '../../../../services/common/LogService';

@Component({
    moduleId: module.id,
    selector: 'sa-visualization',
    templateUrl: './SAVisualization.html',
    styleUrls: ['./SAVisualization.css']
})

export class SAVisualization implements OnInit, OnDestroy {
    class = 'relative';

    @Input()
    job: Job;

    result: Result;

    gradientMaxColor: string = "#1761a8";
    gradientMinColor: string = "#cadef1";
    gradientMaxValue: number = null;
    gradientMinValue: number = null;
    currentNumTopSamples: number = 25;
    signatures: string[] = [];
    selectedSignatures: string[] = [];
    
    saSub: Subscription;

    constructor(
        private _saService: SignatureAnalysisService,
        private _router: Router,
        private _sessionService: SessionService,
        private _logger: LogService) {
    }
    ngOnInit() {
        this.saSub = this._saService.getResult(this.job._id)
            .subscribe(
                (result: Result) => {
                    this.result = result;
                    this.signatures = result.scores.scoreMap.keys();
                    this.selectedSignatures = this.signatures.slice();
                    this.updateGradientMaxAndMinValue();
                },
                (error: any) => {
                    if (error.status == 401) {
                        if (this._router.isActive(this._router.createUrlTree(['/login']), true)) {
                            this._sessionService.redirectToLogin();
                        }
                    } else {
                        alert(`Server error. Try again later`);
                        this._logger.error(error.message, error.stack);
                    }
                });
    }
    ngOnDestroy() {
        this.saSub.unsubscribe();
    }
    updateGradientMaxAndMinValue(): void {
        this.gradientMaxValue = null;
        this.gradientMinValue = 0;
        this.signatures.forEach((signature: string) => {
            let sampleScores: SampleScores = this.result.scores.scoreMap.get(signature);
            let maxKey: string = sampleScores.orderedSampleIds[0];
            let maxValue: number = sampleScores.scoreMap.get(maxKey);
            if (this.gradientMaxValue === null || maxValue > this.gradientMaxValue) {
                this.gradientMaxValue = maxValue;
            }
        });
    }
    updateNumCurrentTopSamples(num: number): void {
        this.currentNumTopSamples = num;
    }
    updateSelectedSignatures(signatures: string[]): void {
        this.selectedSignatures = signatures;
    }
}
