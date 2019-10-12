import {Component, OnInit, OnDestroy, Input} from '@angular/core';
import {Router} from '@angular/router';
import {Subscription} from 'rxjs/Subscription';

import {Job} from '../../../../models/knoweng/Job';
import {FeatureScores, ResponseScores, Result} from '../../../../models/knoweng/results/FeaturePrioritization';
import {FeaturePrioritizationService} from '../../../../services/knoweng/FeaturePrioritizationService';
import {SessionService} from '../../../../services/common/SessionService';
import {LogService} from '../../../../services/common/LogService';

@Component({
    moduleId: module.id,
    selector: 'fp-visualization',
    templateUrl: './FPVisualization.html',
    styleUrls: ['./FPVisualization.css']
})

export class FPVisualization implements OnInit, OnDestroy {
    class = 'relative';

    @Input()
    job: Job;

    result: Result;

    gradientMaxColor: string = "#1761a8";
    gradientMinColor: string = "#cadef1";
    gradientMaxValue: number = null;
    gradientMinValue: number = null;
    currentNumTopFeatures: number = 25;
    responses: string[] = [];
    selectedResponses: string[] = [];
    
    fpSub: Subscription;

    constructor(
        private _fpService: FeaturePrioritizationService,
        private _router: Router,
        private _sessionService: SessionService,
        private _logger: LogService) {
    }
    ngOnInit() {
        this.fpSub = this._fpService.getResult(this.job._id)
            .subscribe(
                (result: Result) => {
                    this.result = result;
                    this.responses = result.scores.scoreMap.keys();
                    this.selectedResponses = this.responses.slice();
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
        this.fpSub.unsubscribe();
    }
    updateGradientMaxAndMinValue(): void {
        this.gradientMaxValue = null;
        this.gradientMinValue = this.result.minimumScore;
        this.responses.forEach((response: string) => {
            let featureScores: FeatureScores = this.result.scores.scoreMap.get(response);
            let maxKey: string = featureScores.orderedFeatureIds[0];
            let maxValue: number = featureScores.scoreMap.get(maxKey);
            if (this.gradientMaxValue === null || maxValue > this.gradientMaxValue) {
                this.gradientMaxValue = maxValue;
            }
        });
    }
    updateNumCurrentTopFeatures(num: number): void {
        this.currentNumTopFeatures = num;
    }
    updateSelectedResponses(responses: string[]): void {
        this.selectedResponses = responses;
    }
}
