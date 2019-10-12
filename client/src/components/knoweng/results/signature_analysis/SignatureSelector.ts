import {Component, Input, OnChanges, SimpleChange, Output, EventEmitter} from '@angular/core';

import {Result} from '../../../../models/knoweng/results/SignatureAnalysis';

@Component ({
    moduleId: module.id,
    selector: 'signature-selector',
    styleUrls: ['./SignatureSelector.css'],
    templateUrl: './SignatureSelector.html'
})

export class SignatureSelector implements OnChanges {
    class = 'relative';

    @Input()
    result: Result;
    
    @Input()
    numTopSamples: number;
    
    @Output()
    selectedSignatures: EventEmitter<string[]> = new EventEmitter<string[]>();

    states: SignatureState[] = [];

    constructor() {
    }

    /** Handles updates to the inputs. */
    ngOnChanges(changes: {[propertyName: string]: SimpleChange}) {
        this.states = this.result.scores.scoreMap.keys().sort().map((signature: string) => new SignatureState(signature, true));
    }
    getSelectedStates(): string[] {
        return this.states.filter((state) => state.selected).map((state) => state.signature);
    }
    onOneClicked(state: SignatureState): void {
        state.selected = !state.selected;
        this.selectedSignatures.emit(this.getSelectedStates());
    }
    onAllClicked(): void {
        let currentTotal: number = this.states.length;
        let currentSelected: number = this.getSelectedStates().length;
        if (currentTotal == currentSelected) {
            // all are selected; deselect all
            this.states.forEach((state) => state.selected = false);
        } else {
            // select all
            this.states.forEach((state) => state.selected = true);
        }
        this.selectedSignatures.emit(this.getSelectedStates());
    }
}

class SignatureState {
    constructor(
        public signature: string,
        public selected: boolean) {
    }
}