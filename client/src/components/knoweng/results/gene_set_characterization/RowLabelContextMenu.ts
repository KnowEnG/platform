import {Component, OnChanges, SimpleChange, Input, Output, EventEmitter} from '@angular/core';

import {UserGeneSet} from '../../../../models/knoweng/results/GeneSetCharacterization';

@Component({
    moduleId: module.id,
    selector: 'row-label-context-menu',
    templateUrl: './LabelContextMenu.html',
    styleUrls: ['./LabelContextMenu.css']
})

export class RowLabelContextMenu implements OnChanges {
    class = 'relative';

    @Input()
    userGeneSet: UserGeneSet;

    @Output()
    sort: EventEmitter<UserGeneSet> = new EventEmitter<UserGeneSet>();

    title: string;
    subtitle: string;
    geneCount: number;
    sortDimension = "Row";

    constructor() {
    }
    ngOnChanges(changes: {[propertyName: string]: SimpleChange}) {
        this.title = this.userGeneSet.name;
        this.subtitle = "Your Gene Set";
        this.geneCount = this.userGeneSet.geneIds.length;
    }
    onSort() {
        this.sort.emit(this.userGeneSet);
    }
}
