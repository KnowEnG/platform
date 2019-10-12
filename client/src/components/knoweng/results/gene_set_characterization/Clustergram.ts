import {Component, OnChanges, SimpleChange, Input, Output, EventEmitter} from '@angular/core';

import {ComparisonGeneSet, UserGeneSet, ComparisonGeneSetScores, UserGeneSetScores, GeneSetLevelScore, Result, DISPLAY_DATA_REGISTRY} from '../../../../models/knoweng/results/GeneSetCharacterization';
import {CellHeatmapEvent} from '../common/CellHeatmap';

@Component({
    moduleId: module.id,
    selector: 'clustergram',
    templateUrl: './Clustergram.html',
    styleUrls: ['./Clustergram.css']
})

export class Clustergram implements OnChanges {
    class = 'relative';

    @Input()
    gradientMaxColor: string;

    @Input()
    gradientMinColor: string;

    @Input()
    gradientMaxThreshold: number;

    @Input()
    gradientMinThreshold: number;

    @Input()
    gradientCurrentThreshold: number;

    @Input()
    comparisonGeneSets: ComparisonGeneSet[];

    @Input()
    selectedUserGeneSets: UserGeneSet[];

    @Input()
    selectedComparisonGeneSets: ComparisonGeneSet[];

    @Input()
    result: Result;

    showGeneSetLevelRollover: boolean = false;
    showGeneLevelRollover: boolean = false;
    showRowLabelContextMenu: boolean = false;
    showColumnLabelContextMenu: boolean = false;

    geneSetLevelHoverRowIndex: number = null;
    geneSetLevelHoverColumnIndex: number = null;
    geneSetLevelRolloverRowIndex: number = null;
    geneSetLevelRolloverColumnIndex: number = null;
    geneSetLevelRolloverScore: GeneSetLevelScore = null;

    rowContextMenuIndex: number = null;
    columnContextMenuIndex: number = null;

    rolloverBottom: number = null;
    rolloverRight: number = null;

    defaultColor = '#EEEEEE'; // 0x607?

    rowsOfColumns: string[][] = null;

    displayDataRegistry = DISPLAY_DATA_REGISTRY;

    rowScores: number[] = null;
    columnScores: number[] = null;
    columnSupercollectionMerged: boolean[] = null;

    /** "Alphabet" or "Score" or "Similarity" or one of the comparison gene sets */
    sortRowsBy: string | ComparisonGeneSet = "Alphabet";
    /** "Alphabet" or "Score" or "Similarity" or one of the user gene sets */
    sortColumnsBy: string | UserGeneSet = "Score";

    // DEBUG ONLY: Set to true to show additional debug 
    //     buttons in the UI for testing performance
    DEBUG: boolean = false;
    
    // DEBUG ONLY: Trigger our current redraw function manually
    //     NOTE: this should trigger the same detection as testRedrawFullCopy()
    testRedrawExisting() {
        console.time('redraw_current');
        this.redraw();
        console.timeEnd('redraw_current');
    }
    
    // DEBUG ONLY: Test ChangeDetection by copying each sub-array within a 
    //     nested array to a new reference
    testRedrawLayerCopy() {
        if (!this.rowsOfColumns) {
            return;
        }
        console.time('redraw_single');
        
        // Copy/assign first layer in multi-dimensional array
        this.rowsOfColumns.forEach(row => {
            let copy = Object.assign([], row);
            row = copy;
        });
        console.timeEnd('redraw_single');
    }
    
    // DEBUG ONLY: Test ChangeDetection by copying the outer array of a nested
    //     array into a new reference
    testRedrawFullCopy() {
        if (!this.rowsOfColumns) {
            return;
        }
        console.time('redraw_full');
        
        // Copy/assign full array over the top of existing one
        let copy = Object.assign([], this.rowsOfColumns);
        this.rowsOfColumns = copy;
        console.timeEnd('redraw_full');
    }
    
    comparisonGeneSetsCountMessageMapping: {[k: string]: string} = {
        '=0': 'NO COLLECTIONS',
        '=1': '1 COLLECTION',
        'other': '# COLLECTIONS'
    };
    userGeneSetsCountMessageMapping: {[k: string]: string} = {
        '=0': 'NO GENE SETS',
        '=1': '1 GENE SET',
        'other': '# GENE SETS'
    };

    constructor() {
    }
    ngOnChanges(changes: {[propertyName: string]: SimpleChange}) {
        this.redraw();
    }
    redraw(): void {
        this.closeRollover();
        this.sortTable();

        let interpolate: any = d3.interpolateRgb(this.gradientMinColor, this.gradientMaxColor);
        let scale: any = d3.scale.linear().domain([this.gradientMinThreshold, this.gradientMaxThreshold]).range([0, 1]);
        let comparisonGeneSetScores: ComparisonGeneSetScores = this.result.setLevelScores;
        
        // Since we do this as a single assignment, rather than incrementally, 
        //    we shouldn't need to worry about excessive ChangeDetection here
        this.rowsOfColumns =
            this.selectedUserGeneSets.map((ugs: UserGeneSet) => {
                return this.selectedComparisonGeneSets.map((cgs: ComparisonGeneSet) => {
                    let userGeneSetScores: UserGeneSetScores =
                        comparisonGeneSetScores.scoreMap.get(cgs.knId);
                    let color = this.defaultColor;
                    if (userGeneSetScores.scoreMap.has(ugs.name)) {
                        let score = userGeneSetScores.scoreMap.get(ugs.name).shadingScore;
                        color = interpolate(scale(score));
                    }
                    return color;
                });
            });

        let maxPerRow: number[] = this.selectedUserGeneSets.map((ugs: UserGeneSet) => {
            return comparisonGeneSetScores.getMaxGeneSetLevelScoreForUserGeneSet(
                this.selectedComparisonGeneSets.map((cgs: ComparisonGeneSet) => cgs.knId), ugs.name);
        });
        let maxPerColumn: number[] = this.selectedComparisonGeneSets.map((cgs: ComparisonGeneSet) => {
            return comparisonGeneSetScores.getMaxGeneSetLevelScoreForComparisonGeneSet(
                cgs.knId, this.selectedUserGeneSets.map((ugs: UserGeneSet) => ugs.name));
        });
        let tableMax: number = d3.max(maxPerRow);
        // TODO FIXME can't assume 0 is the right score
        this.rowScores = maxPerRow.map((val: number) => (isNaN(val) || tableMax == 0) ? 0 : val/tableMax);
        this.columnScores = maxPerColumn.map((val: number) => (isNaN(val) || tableMax == 0) ? 0 : val/tableMax);

        this.columnSupercollectionMerged = this.selectedComparisonGeneSets.map((cgs: ComparisonGeneSet, index: number) => {
            return index == 0 || cgs.supercollectionName == this.selectedComparisonGeneSets[index-1].supercollectionName;
        });
    }
    sortTable(): void {
        if (this.sortRowsBy == "Alphabet") {
            this.selectedUserGeneSets = this.selectedUserGeneSets.slice().sort((a: UserGeneSet, b: UserGeneSet) => {
                return d3.ascending(a.name.toLowerCase(), b.name.toLowerCase());
            });
        } else if (this.sortRowsBy == "Score") {
            let comparisonGeneSetScores: ComparisonGeneSetScores = this.result.setLevelScores;
            this.selectedUserGeneSets = this.selectedUserGeneSets.slice().sort((a: UserGeneSet, b: UserGeneSet) => {
                return d3.descending(
                    comparisonGeneSetScores.getMaxGeneSetLevelScoreForUserGeneSet(
                        this.selectedComparisonGeneSets.map((cgs: ComparisonGeneSet) => cgs.knId), a.name) || 0,
                    comparisonGeneSetScores.getMaxGeneSetLevelScoreForUserGeneSet(
                        this.selectedComparisonGeneSets.map((cgs: ComparisonGeneSet) => cgs.knId), b.name) || 0);
            });
        } else if (this.sortRowsBy == "Similarity") {
            alert("TODO");
        } else {
            let knId: string = (<ComparisonGeneSet>this.sortRowsBy).knId;
            let userGeneSetScores: UserGeneSetScores = this.result.setLevelScores.scoreMap.get(knId);
            this.selectedUserGeneSets = this.selectedUserGeneSets.slice().sort((a: UserGeneSet, b: UserGeneSet) => {
                let scoreA: number = null;
                let scoreB: number = null;
                if (userGeneSetScores.scoreMap.has(a.name)) {
                    scoreA = userGeneSetScores.scoreMap.get(a.name).shadingScore;
                }
                if (userGeneSetScores.scoreMap.has(b.name)) {
                    scoreB = userGeneSetScores.scoreMap.get(b.name).shadingScore;
                }
                return d3.descending(scoreA, scoreB);
            });
        }

        if (this.sortColumnsBy == "Alphabet") {
            // TODO how to handle supercollections, which have their own order?
            this.selectedComparisonGeneSets = this.selectedComparisonGeneSets.slice().sort((a: ComparisonGeneSet, b: ComparisonGeneSet) => {
                return d3.ascending(a.name.toLowerCase(), b.name.toLowerCase());
            });
        } else if (this.sortColumnsBy == "Score") {
            let comparisonGeneSetScores: ComparisonGeneSetScores = this.result.setLevelScores;
            this.selectedComparisonGeneSets = this.selectedComparisonGeneSets.slice().sort((a: ComparisonGeneSet, b: ComparisonGeneSet) => {
                return d3.descending(
                    comparisonGeneSetScores.getMaxGeneSetLevelScoreForComparisonGeneSet(
                        a.knId, this.selectedUserGeneSets.map((ugs: UserGeneSet) => ugs.name)),
                    comparisonGeneSetScores.getMaxGeneSetLevelScoreForComparisonGeneSet(
                        b.knId, this.selectedUserGeneSets.map((ugs: UserGeneSet) => ugs.name)));
            });
        } else if (this.sortColumnsBy == "Similarity") {
            alert("TODO");
        } else {
            let userGeneSetName: string = (<UserGeneSet>this.sortColumnsBy).name;
            this.selectedComparisonGeneSets = this.selectedComparisonGeneSets.slice().sort((a: ComparisonGeneSet, b: ComparisonGeneSet) => {
                let comparisonGeneSetScores: ComparisonGeneSetScores = this.result.setLevelScores;
                let scoreA: number = null;
                let scoreB: number = null;
                // TODO refactor; this'd be better in model
                if (comparisonGeneSetScores.scoreMap.has(a.knId)) {
                    let userGeneSetScores: UserGeneSetScores = comparisonGeneSetScores.scoreMap.get(a.knId);
                    if (userGeneSetScores.scoreMap.has(userGeneSetName)) {
                        scoreA = userGeneSetScores.scoreMap.get(userGeneSetName).shadingScore;
                    }
                }
                if (comparisonGeneSetScores.scoreMap.has(b.knId)) {
                    let userGeneSetScores: UserGeneSetScores = comparisonGeneSetScores.scoreMap.get(b.knId);
                    if (userGeneSetScores.scoreMap.has(userGeneSetName)) {
                        scoreB = userGeneSetScores.scoreMap.get(userGeneSetName).shadingScore;
                    }
                }
                return d3.descending(scoreA, scoreB);
            });
        }
    }
    onRowLabelContextMenu(rowIndex: number, event: MouseEvent): void {
        event.preventDefault();
        this.closeRollover();
        this.showRowLabelContextMenu = true;
        this.rowContextMenuIndex = rowIndex;
        this.setRolloverCorners(event);
    }
    onColumnLabelContextMenu(columnIndex: number, event: MouseEvent): void {
        event.preventDefault();
        this.closeRollover();
        this.showColumnLabelContextMenu = true;
        this.columnContextMenuIndex = columnIndex;
        this.setRolloverCorners(event);
    }
    onCellClicked(selection: CellHeatmapEvent) {
        this.closeRollover();
        this.showGeneSetLevelRollover = true;
        this.geneSetLevelRolloverRowIndex = selection.rowIndex;
        this.geneSetLevelRolloverColumnIndex = selection.colIndex;
        this.geneSetLevelHoverRowIndex = selection.rowIndex;
        this.geneSetLevelHoverColumnIndex = selection.colIndex;

        let comparisonGeneSet: ComparisonGeneSet = this.selectedComparisonGeneSets[selection.colIndex];
        let userGeneSet: UserGeneSet = this.selectedUserGeneSets[selection.rowIndex];
        let userGeneSetScores: UserGeneSetScores = this.result.setLevelScores.scoreMap.get(comparisonGeneSet.knId);
        if (userGeneSetScores.scoreMap.has(userGeneSet.name)) {
            this.geneSetLevelRolloverScore = userGeneSetScores.scoreMap.get(userGeneSet.name);
        } else {
            this.geneSetLevelRolloverScore = null;
        }

        this.setRolloverCorners(selection.event);
    }
    onCellMousedOver(selection: CellHeatmapEvent) {
        if (!this.showGeneSetLevelRollover) {
            this.geneSetLevelHoverRowIndex = selection.rowIndex;
            this.geneSetLevelHoverColumnIndex = selection.colIndex;
        }
    }
    onSortColumnsByRow(userGeneSet: UserGeneSet): void {
        this.closeRollover();
        this.sortColumnsBy = userGeneSet;
        this.redraw();
    }
    onSortRowsByColumn(comparisonGeneSet: ComparisonGeneSet): void {
        this.closeRollover();
        this.sortRowsBy = comparisonGeneSet;
        this.redraw();
    }
    onSortColumnsByOther(sort: string): void {
        this.closeRollover();
        this.sortColumnsBy = sort;
        this.redraw();
    }
    onSortRowsByOther(sort: string): void {
        this.closeRollover();
        this.sortRowsBy = sort;
        this.redraw();
    }
    setRolloverCorners(event: MouseEvent) {
        this.rolloverBottom = window.innerHeight - event.clientY - 85; // 85 looks good on the screen; no science to it
        if (this.rolloverBottom < 0) {
            this.rolloverBottom = 0;
        }
        this.rolloverRight = window.innerWidth - event.clientX - 15; // 15 looks good on the screen; no science to it
    }
    closeRollover() {
        this.showGeneSetLevelRollover = false;
        this.geneSetLevelRolloverRowIndex = null;
        this.geneSetLevelRolloverColumnIndex = null;
        this.geneSetLevelRolloverScore = null;

        this.showGeneLevelRollover = false;

        this.showRowLabelContextMenu = false;
        this.rowContextMenuIndex = null;

        this.showColumnLabelContextMenu = false;
        this.columnContextMenuIndex = null;
    }
}
