import {Component, OnChanges, SimpleChange, Input, Output, EventEmitter} from '@angular/core';

import {Job} from '../../../../models/knoweng/Job';
import {ComparisonGeneSet, ComparisonGeneSetCollection, ComparisonGeneSetSupercollection, ComparisonGeneSetScores, UserGeneSet, Result} from '../../../../models/knoweng/results/GeneSetCharacterization';

@Component({
    moduleId: module.id,
    selector: 'gsc-control-panel',
    templateUrl: './ControlPanel.html',
    styleUrls: ['./ControlPanel.css']
})

export class ControlPanel implements OnChanges {
    class = 'relative';

    @Input()
    job: Job;

    @Input()
    gradientMaxColor: string;

    @Input()
    gradientMinColor: string;

    @Input()
    gradientMaxThreshold: number;

    @Input()
    gradientMinThreshold: number;

    @Input()
    gradientCurrentThreshold: number;

    @Input()
    userGeneSets: UserGeneSet[];

    @Input()
    comparisonGeneSets: ComparisonGeneSet[];

    @Input()
    result: Result;

    @Output()
    selectedComparisonGeneSets: EventEmitter<ComparisonGeneSet[]> = new EventEmitter<ComparisonGeneSet[]>();

    @Output()
    selectedUserGeneSets: EventEmitter<UserGeneSet[]> = new EventEmitter<UserGeneSet[]>();

    @Output()
    updateThreshold: EventEmitter<number> = new EventEmitter<number>();

    candidateComparisonGeneSets: ComparisonGeneSet[] = [];

    constructor() {
    }
    ngOnChanges(changes: {[propertyName: string]: SimpleChange}) {
        this.updateCandidateComparisonGeneSets();
    }
    updateSelectedUserGeneSets(selectedUserGeneSets: UserGeneSet[]) {
        this.selectedUserGeneSets.emit(selectedUserGeneSets);
    }
    updateSelectedComparisonGeneSets(selectedComparisonGeneSets: ComparisonGeneSet[]) {
        this.selectedComparisonGeneSets.emit(selectedComparisonGeneSets);
    }
    updateGradientCurrentThreshold(threshold: number) {
        this.gradientCurrentThreshold = threshold;
        this.updateThreshold.emit(threshold);
        this.updateCandidateComparisonGeneSets();
    }
    updateCandidateComparisonGeneSets(): void {
        let setLevelScores: ComparisonGeneSetScores = this.result.setLevelScores;
        this.candidateComparisonGeneSets = this.comparisonGeneSets.filter((cgs: ComparisonGeneSet) => {
            return setLevelScores.scoreMap.get(cgs.knId).getMaxGeneSetLevelScore(this.userGeneSets.map((ugs: UserGeneSet) => ugs.name)) > this.gradientCurrentThreshold;
        });
    }
}
