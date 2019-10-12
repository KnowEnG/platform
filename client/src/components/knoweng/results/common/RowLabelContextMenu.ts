import {Component, OnChanges, SimpleChange, Input, Output, EventEmitter} from '@angular/core';

@Component({
    moduleId: module.id,
    selector: 'row-label-context-menu',
    templateUrl: './LabelContextMenu.html',
    styleUrls: ['./LabelContextMenu.css']
})

export class RowLabelContextMenu implements OnChanges {
    class = 'relative';

    @Input()
    title: string;

    @Input()
    value: string;

    @Output()
    sort: EventEmitter<string> = new EventEmitter<string>();

    sortDimension = "Row";

    constructor() {
    }
    ngOnChanges(changes: {[propertyName: string]: SimpleChange}) {
    }
    onSort() {
        this.sort.emit(this.value);
    }
}
