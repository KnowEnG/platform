import {Component, OnInit, EventEmitter, Output, Input} from '@angular/core';

@Component({
    moduleId: module.id,
    selector: 'textbox-editor-modal',
    templateUrl: './TextboxEditorModal.html',
    styleUrls: ['./TextboxEditorModal.css']
})

export class TextboxEditorModal implements OnInit {
    class = 'relative';
    
    @Input()
    initialValue: string;

    @Output()
    save: EventEmitter<string> = new EventEmitter<string>();

    @Output()
    cancel: EventEmitter<string> = new EventEmitter<string>();

    currentValue: string;

    constructor() {
    }
    ngOnInit() {
        this.currentValue = this.initialValue;
    }
    onTextBlur(event: Event) {
        this.currentValue = (<any>event.target).value;
    }
    onSave() {
        this.save.emit(this.currentValue);
    }
    onCancel() {
        this.cancel.emit(this.initialValue);
    }
}
