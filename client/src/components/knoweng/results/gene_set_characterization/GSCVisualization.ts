import {Component, OnInit, Input, ChangeDetectorRef} from '@angular/core';
import {Router} from '@angular/router';
import {Subscription} from 'rxjs/Subscription';

import {Job} from '../../../../models/knoweng/Job';
import {LogService} from '../../../../services/common/LogService';
import {SessionService} from '../../../../services/common/SessionService';
import {ComparisonGeneSet, UserGeneSet, Result} from '../../../../models/knoweng/results/GeneSetCharacterization';
import {GeneSetCharacterizationService} from '../../../../services/knoweng/GeneSetCharacterizationService';

import 'rxjs/add/observable/from';

@Component({
    moduleId: module.id,
    selector: 'gsc-visualization',
    templateUrl: './GSCVisualization.html',
    styleUrls: ['./GSCVisualization.css']
})

export class GSCVisualization implements OnInit {
    class = 'relative';

    @Input()
    job: Job;

    result: Result;

    gradientMaxColor: string = "#1761a8";
    gradientMinColor: string = "#cadef1";
    gradientMaxThreshold: number = null;
    gradientMinThreshold: number = null;
    gradientCurrentThreshold: number = null;

    userGeneSets: UserGeneSet[] = [];
    selectedUserGeneSets: UserGeneSet[] = [];

    comparisonGeneSets: ComparisonGeneSet[] = [];
    selectedComparisonGeneSets: ComparisonGeneSet[] = [];
    resultSub: Subscription;
    geneSub: Subscription;

    constructor(
        private _gscService: GeneSetCharacterizationService,
        private _router: Router,
        private _sessionService: SessionService,
        private _logger: LogService,
        private _changeDetector: ChangeDetectorRef) {
    }
    ngOnInit() {
        this.resultSub = this._gscService.getResult(this.job._id)
            .subscribe(
                (result: Result) => {
                    this.result = result;
                    this.userGeneSets = result.userGeneSets;
                    this.selectedUserGeneSets = result.userGeneSets.slice();
                    this.fetchComparisonGeneSets();
                    this.updateMaxAndMinThresholds();
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
        this.resultSub.unsubscribe();
        this.geneSub.unsubscribe();
        
        this.result = undefined;
        this.job = undefined;
        this.userGeneSets = undefined;
        this.selectedUserGeneSets = undefined;
        this.comparisonGeneSets = undefined;
        this.selectedComparisonGeneSets = undefined;
    }
    fetchComparisonGeneSets(): void {
        let setIds: string[] = this.result.setLevelScores.scoreMap.keys();
        this.geneSub = this._gscService.getComparisonGeneSets(setIds, this.job.parameters.species)
            .subscribe(
                (comparisonGeneSets: ComparisonGeneSet[]) => {
                    this.comparisonGeneSets = comparisonGeneSets;
                    this.selectedComparisonGeneSets = comparisonGeneSets.slice();
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
    updateMaxAndMinThresholds(): void {
        // we use the scoreMap's keys instead of this.comparisonGeneSets because
        // this.comparisonGeneSets may not be loaded from the server yet
        this.gradientMaxThreshold = this.result.setLevelScores.getMaxGeneSetLevelScore(
            this.result.setLevelScores.scoreMap.keys(),
            this.userGeneSets.map((ugs: UserGeneSet) => ugs.name));
        this.gradientMinThreshold = this.result.minimumScore;
        this.gradientCurrentThreshold = d3.scale.linear().domain([0, 1]).range([this.gradientMinThreshold, this.gradientMaxThreshold])(.75);
        this._changeDetector.detectChanges();
    }
    updateSelectedComparisonGeneSets(selected: ComparisonGeneSet[]) {
        this.selectedComparisonGeneSets = selected;
    }
    updateSelectedUserGeneSets(selected: UserGeneSet[]) {
        this.selectedUserGeneSets = selected;
    }
    updateThreshold(threshold: number) {
        this.gradientCurrentThreshold = threshold;
    }
}
