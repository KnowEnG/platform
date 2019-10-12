import {Component, Input, OnChanges, SimpleChange, Output, EventEmitter} from '@angular/core';

import {Result} from '../../../../models/knoweng/results/FeaturePrioritization';

@Component ({
    moduleId: module.id,
    selector: 'response-selector',
    styleUrls: ['./ResponseSelector.css'],
    templateUrl: './ResponseSelector.html'
})

export class ResponseSelector implements OnChanges {
    class = 'relative';

    @Input()
    result: Result;
    
    @Input()
    numTopFeatures: number;
    
    @Output()
    selectedResponses: EventEmitter<string[]> = new EventEmitter<string[]>();

    states: ResponseState[] = [];

    constructor() {
    }

    /** Handles updates to the inputs. */
    ngOnChanges(changes: {[propertyName: string]: SimpleChange}) {
        if (changes.hasOwnProperty("result")) {
            this.states = this.result.scores.scoreMap.keys().sort().map((response: string) => new ResponseState(response, true));
        }
    }
    getSelectedStates(): string[] {
        return this.states.filter((state: ResponseState) => state.selected).map((state: ResponseState) => state.response);
    }
    onOneClicked(state: ResponseState): void {
        state.selected = !state.selected;
        this.selectedResponses.emit(this.getSelectedStates());
    }
    onAllClicked(): void {
        let currentTotal: number = this.states.length;
        let currentSelected: number = this.getSelectedStates().length;
        if (currentTotal == currentSelected) {
            // all are selected; deselect all
            this.states.forEach((state: ResponseState) => state.selected = false);
        } else {
            // select all
            this.states.forEach((state: ResponseState) => state.selected = true);
        }
        this.selectedResponses.emit(this.getSelectedStates());
    }
}

class ResponseState {
    constructor(
        public response: string,
        public selected: boolean) {
    }
}