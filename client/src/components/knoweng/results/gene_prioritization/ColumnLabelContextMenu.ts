import {Component, OnChanges, SimpleChange, Input, Output, EventEmitter} from '@angular/core';

@Component({
    moduleId: module.id,
    selector: 'column-label-context-menu',
    templateUrl: './LabelContextMenu.html',
    styleUrls: ['./LabelContextMenu.css']
})

export class ColumnLabelContextMenu implements OnChanges {
    class = 'relative';

    @Input()
    title: string;

    @Output()
    sort: EventEmitter<string> = new EventEmitter<string>();

    sortDimension = "Column";

    constructor() {
    }
    ngOnChanges(changes: {[propertyName: string]: SimpleChange}) {
    }
    onSort() {
        this.sort.emit(this.title);
    }
}
