import {Component, Input, Output, EventEmitter} from '@angular/core';

// note: as of this writing, we're on ngx-bootstrap 1.6.6
// later versions have better modal apis that'd allow us to simplify

@Component({
    moduleId: module.id,
    selector: 'error-modal',
    templateUrl: './ErrorModal.html',
    styleUrls: ['./ErrorModal.css']
})

export class ErrorModal {
    @Input()
    header: string;

    @Input()
    body: string;

    @Output()
    closeMe: EventEmitter<void> = new EventEmitter<void>();
}

