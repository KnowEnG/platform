import {Component, OnChanges, SimpleChange, Input, Output, EventEmitter} from '@angular/core';

import {ComparisonGeneSet, UserGeneSet, GeneSetLevelScore, DISPLAY_DATA_REGISTRY} from '../../../../models/knoweng/results/GeneSetCharacterization';

@Component({
    moduleId: module.id,
    selector: 'gene-set-level-rollover',
    templateUrl: './GeneSetLevelRollover.html',
    styleUrls: ['./GeneSetLevelRollover.css']
})

export class GeneSetLevelRollover implements OnChanges {
    class = 'relative';

    @Input()
    gradientMaxColor: string;

    @Input()
    gradientMinColor: string;

    @Input()
    gradientMaxThreshold: number;

    @Input()
    gradientMinThreshold: number;

    @Input()
    geneSetLevelScore: GeneSetLevelScore;

    @Input()
    comparisonGeneSet: ComparisonGeneSet;

    @Input()
    userGeneSet: UserGeneSet;

    @Output()
    close: EventEmitter<boolean> = new EventEmitter<boolean>();

    piePercentage: number = null;

    comparisonColor: string = null;

    constructor() {
    }
    ngOnChanges(changes: {[propertyName: string]: SimpleChange}) {
        // TODO: note there's logic here and in the template to cover case where
        // geneSetLevelScore is null, which currently happens for cells whose
        // scores fall below the threshold set on the backend
        // need to clarify requirements, but we may end up with scores for all
        // set-level cells in order to implement gene-level drilldown
        // if that's the case, revisit these null checks
        if (this.geneSetLevelScore !== null) {
            this.piePercentage = 100 * this.geneSetLevelScore.overlapCount / this.comparisonGeneSet.geneCount;
        } else {
            this.piePercentage = 0;
        }
        this.comparisonColor = DISPLAY_DATA_REGISTRY[this.comparisonGeneSet.supercollectionName].color;
    }
    onClose() {
        this.close.emit(true);
    }
}
