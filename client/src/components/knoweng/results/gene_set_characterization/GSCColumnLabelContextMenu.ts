import {Component, OnChanges, SimpleChange, Input, Output, EventEmitter} from '@angular/core';

import {ComparisonGeneSet} from '../../../../models/knoweng/results/GeneSetCharacterization';

@Component({
    moduleId: module.id,
    selector: 'gsc-column-label-context-menu',
    templateUrl: './GSCLabelContextMenu.html',
    styleUrls: ['./GSCLabelContextMenu.css']
})

export class GSCColumnLabelContextMenu implements OnChanges {
    class = 'relative';

    @Input()
    comparisonGeneSet: ComparisonGeneSet;

    @Output()
    sort: EventEmitter<ComparisonGeneSet> = new EventEmitter<ComparisonGeneSet>();

    title: string;
    subtitle: string;
    geneCount: number;
    sortDimension = "Column";

    constructor() {
    }
    ngOnChanges(changes: {[propertyName: string]: SimpleChange}) {
        this.title = this.comparisonGeneSet.knId;
        this.subtitle = this.comparisonGeneSet.collectionName;
        this.geneCount = this.comparisonGeneSet.geneCount;
    }
    onSort() {
        this.sort.emit(this.comparisonGeneSet);
    }
}
