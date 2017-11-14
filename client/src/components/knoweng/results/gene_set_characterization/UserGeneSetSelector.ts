import {Component, Input, OnChanges, SimpleChange, Output, EventEmitter} from '@angular/core';

import {UserGeneSet} from '../../../../models/knoweng/results/GeneSetCharacterization';

@Component ({
    moduleId: module.id,
    selector: 'user-gene-set-selector',
    styleUrls: ['./UserGeneSetSelector.css'],
    templateUrl: './UserGeneSetSelector.html'
})

export class UserGeneSetSelector implements OnChanges {
    class = 'relative';

    @Input()
    jobName: string;

    @Input()
    userGeneSets: UserGeneSet[];

    @Output()
    selectedUserGeneSets: EventEmitter<UserGeneSet[]> = new EventEmitter<UserGeneSet[]>();

    open: boolean = false;

    states: UserGeneSetState[] = [];

    constructor() {
    }

    /** Handles updates to the inputs. */
    ngOnChanges(changes: {[propertyName: string]: SimpleChange}) {
        this.states = this.userGeneSets.map((ugs: UserGeneSet) => new UserGeneSetState(ugs, true));
    }
    getSelectedStates(): UserGeneSet[] {
        return this.states.filter((state: UserGeneSetState) => state.selected).map((state: UserGeneSetState) => state.userGeneSet);
    }
    onOneClicked(state: UserGeneSetState): void {
        state.selected = !state.selected;
        this.selectedUserGeneSets.emit(this.getSelectedStates());
    }
    onAllClicked(): void {
        let currentTotal: number = this.states.length;
        let currentSelected: number = this.getSelectedStates().length;
        if (currentTotal == currentSelected) {
            // all are selected; deselect all
            this.states.forEach((state: UserGeneSetState) => state.selected = false);
        } else {
            // select all
            this.states.forEach((state: UserGeneSetState) => state.selected = true);
        }
        this.selectedUserGeneSets.emit(this.getSelectedStates());
    }
}

class UserGeneSetState {
    constructor(
        public userGeneSet: UserGeneSet,
        public selected: boolean) {
    }
}