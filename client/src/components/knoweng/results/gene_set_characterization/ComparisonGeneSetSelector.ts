import {Component, Input, OnChanges, SimpleChange, Output, EventEmitter} from '@angular/core';

import {ComparisonGeneSet, ComparisonGeneSetCollection, ComparisonGeneSetSupercollection} from '../../../../models/knoweng/results/GeneSetCharacterization';

@Component ({
    moduleId: module.id,
    selector: 'comparison-gene-set-selector',
    styleUrls: ['./ComparisonGeneSetSelector.css'],
    templateUrl: './ComparisonGeneSetSelector.html'
})

export class ComparisonGeneSetSelector implements OnChanges {
    class = 'relative';

    @Input()
    comparisonGeneSets: ComparisonGeneSet[];

    @Output()
    selectedComparisonGeneSets: EventEmitter<ComparisonGeneSet[]> = new EventEmitter<ComparisonGeneSet[]>();

    supercollectionStates: SupercollectionState[] = [];

    constructor() {
    }

    /** Handles updates to the inputs. */
    ngOnChanges(changes: {[propertyName: string]: SimpleChange}) {
        this.supercollectionStates = ComparisonGeneSetSupercollection
            .fromComparisonGeneSets(this.comparisonGeneSets)
            .map((supercollection: ComparisonGeneSetSupercollection) => new SupercollectionState(supercollection, false));
        this.selectedComparisonGeneSets.emit(this.getSelectedGeneSets());
    }
    /** Returns all selected gene sets. */
    getSelectedGeneSets(): ComparisonGeneSet[] {
        let returnVal: ComparisonGeneSet[] = [];
        this.supercollectionStates.forEach((supercollectionState: SupercollectionState) => {
            supercollectionState.collectionStates.forEach((collectionState: CollectionState) => {
                collectionState.geneSetStates.forEach((geneSetState: GeneSetState) => {
                    if (geneSetState.selected) {
                        returnVal.push(geneSetState.geneSet);
                    }
                })
            });
        });
        return returnVal;
    }
    /** Opens/closes supercollection level */
    toggleSupercollectionOpen(supercollectionState: SupercollectionState): void {
        supercollectionState.open = !supercollectionState.open;
    }
    /** Selects all/deselects all at supercollection level */
    onSupercollectionChecked(supercollectionState: SupercollectionState): void {
        if (supercollectionState.getSelectedCount() == supercollectionState.getTotalCount()) {
            // all are selected; deselect all
            supercollectionState.deselectAll();
        } else {
            // select all
            supercollectionState.selectAll();
        }
        this.selectedComparisonGeneSets.emit(this.getSelectedGeneSets());
    }
    /** Opens/closes collection level */
    toggleCollectionOpen(collectionState: CollectionState): void {
        collectionState.open = !collectionState.open;
    }
    /** Selects all/deselects all at collection level */
    onCollectionChecked(collectionState: CollectionState): void {
        if (collectionState.getSelectedCount() == collectionState.getTotalCount()) {
            // all are selected; deselect all
            collectionState.deselectAll();
        } else {
            // select all
            collectionState.selectAll();
        }
        this.selectedComparisonGeneSets.emit(this.getSelectedGeneSets());
    }
    /** Selects/deselects at gene set level */
    toggleGeneSetSelected(geneSetState: GeneSetState): void {
        geneSetState.selected = !geneSetState.selected;
        this.selectedComparisonGeneSets.emit(this.getSelectedGeneSets());
    }
}

class SupercollectionState {
    collectionStates: CollectionState[];
    constructor(
        public supercollection: ComparisonGeneSetSupercollection,
        public open: boolean) {
        this.collectionStates = supercollection.collections
            .map((collection: ComparisonGeneSetCollection) => new CollectionState(collection, false));
    }
    getSelectedCount(): number {
        return this.collectionStates.reduce((acc: number, cur: CollectionState) => {
            return acc + cur.getSelectedCount();
        }, 0);
    }
    getTotalCount(): number {
        return this.collectionStates.reduce((acc: number, cur: CollectionState) => {
            return acc + cur.getTotalCount();
        }, 0);
    }
    selectAll(): void {
        this.collectionStates.forEach((collectionState: CollectionState) => {
           collectionState.selectAll();
        });
    }
    deselectAll(): void {
        this.collectionStates.forEach((collectionState: CollectionState) => {
           collectionState.deselectAll();
        });
    }
}

class CollectionState {
    geneSetStates: GeneSetState[];
    constructor(
        public collection: ComparisonGeneSetCollection,
        public open: boolean) {
        this.geneSetStates = collection.sets
            .map((geneSet: ComparisonGeneSet) => new GeneSetState(geneSet, true));
    }
    getSelectedCount(): number {
        return this.geneSetStates.reduce((acc: number, cur: GeneSetState) => {
            return acc + (cur.selected ? 1 : 0);
        }, 0);
    }
    getTotalCount(): number {
        return this.geneSetStates.length;
    }
    selectAll(): void {
        this.geneSetStates.forEach((geneSetState: GeneSetState) => {
           geneSetState.selected = true;
        });
    }
    deselectAll(): void {
        this.geneSetStates.forEach((geneSetState: GeneSetState) => {
           geneSetState.selected = false;
        });
    }
}

class GeneSetState {
    constructor(
        public geneSet: ComparisonGeneSet,
        public selected: boolean) {
    }
}