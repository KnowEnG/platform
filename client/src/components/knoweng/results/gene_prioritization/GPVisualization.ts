import {Component, OnInit, OnDestroy, Input} from '@angular/core';
import {Router} from '@angular/router';
import {Subscription} from 'rxjs/Subscription';

import {Job} from '../../../../models/knoweng/Job';
import {GeneScores, ResponseScores, Result} from '../../../../models/knoweng/results/GenePrioritization';
import {GenePrioritizationService} from '../../../../services/knoweng/GenePrioritizationService';
import {SessionService} from '../../../../services/common/SessionService';
import {LogService} from '../../../../services/common/LogService';

@Component({
    moduleId: module.id,
    selector: 'gp-visualization',
    templateUrl: './GPVisualization.html',
    styleUrls: ['./GPVisualization.css']
})

export class GPVisualization implements OnInit, OnDestroy {
    class = 'relative';

    @Input()
    job: Job;

    result: Result;

    gradientMaxColor: string = "#1761a8";
    gradientMinColor: string = "#cadef1";
    gradientMaxValue: number = null;
    gradientMinValue: number = null;
    currentNumTopGenes: number = 25;
    responses: string[] = [];
    selectedResponses: string[] = [];
    
    gpSub: Subscription;

    constructor(
        private _gpService: GenePrioritizationService,
        private _router: Router,
        private _sessionService: SessionService,
        private _logger: LogService) {
    }
    ngOnInit() {
        this.gpSub = this._gpService.getResult(this.job._id)
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
        this.gpSub.unsubscribe();
    }
    updateGradientMaxAndMinValue(): void {
        this.gradientMaxValue = null;
        this.gradientMinValue = this.result.minimumScore;
        this.responses.forEach((response: string) => {
            let geneScores: GeneScores = this.result.scores.scoreMap.get(response);
            let maxKey: string = geneScores.orderedGeneIds[0];
            let maxValue: number = geneScores.scoreMap.get(maxKey);
            if (this.gradientMaxValue === null || maxValue > this.gradientMaxValue) {
                this.gradientMaxValue = maxValue;
            }
        });
    }
    updateNumCurrentTopGenes(num: number): void {
        this.currentNumTopGenes = num;
    }
    updateSelectedResponses(responses: string[]): void {
        this.selectedResponses = responses;
    }
}
