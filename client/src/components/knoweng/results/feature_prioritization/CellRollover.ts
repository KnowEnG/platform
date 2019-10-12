import {Component, OnInit, Input, Output, EventEmitter} from '@angular/core';

@Component({
    moduleId: module.id,
    selector: 'cell-rollover',
    templateUrl: './CellRollover.html',
    styleUrls: ['./CellRollover.css']
})

export class CellRollover implements OnInit {
    class = 'relative';

    @Input()
    featureName: string;

    @Input()
    responseName: string;

    @Input()
    finalScore: number;

    @Output()
    close: EventEmitter<boolean> = new EventEmitter<boolean>();

    constructor() {
    }
    ngOnInit() {
    }
    onClose() {
        this.close.emit(true);
    }
}
