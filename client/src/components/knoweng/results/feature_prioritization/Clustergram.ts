import {Component, OnChanges, SimpleChange, Input, Output, EventEmitter} from '@angular/core';

import {FeatureScores, ResponseScores} from '../../../../models/knoweng/results/FeaturePrioritization';

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
    gradientMaxValue: number;

    @Input()
    gradientMinValue: number;

    @Input()
    currentNumTopFeatures: number;

    @Input()
    selectedResponses: string[];

    @Input()
    scores: ResponseScores;

    @Input()
    featureIdToNameMap: d3.Map<string>;

    defaultColor = '#EEEEEE'; // 0x607?

    showRollover: boolean = false;
    showRowLabelContextMenu: boolean = false;
    showColumnLabelContextMenu: boolean = false;

    hoverRowIndex: number = null;
    hoverColumnIndex: number = null;
    rolloverRowIndex: number = null;
    rolloverColumnIndex: number = null;
    rolloverValue: number = null;

    rowContextMenuIndex: number = null;
    columnContextMenuIndex: number = null;

    rolloverBottom: number = null;
    rolloverRight: number = null;

    rowsOfColumns: string[][] = null;
    topFeatureIds: string[] = null;

    rowScores: number[] = null;
    columnScores: number[] = null;

    /** "Alphabet" or "Score" or "Similarity" or one of the feature ids */
    sortRowsBy: string = "Score";
    /** "Alphabet" or "Score" or "Similarity" or one of the response names */
    sortColumnsBy: string = "Alphabet";

    responsesCountMessageMapping: {[k: string]: string} = {
        '=0': 'NO RESPONSES',
        '=1': '1 RESPONSE',
        'other': '# RESPONSES'
    };
    featuresCountMessageMapping: {[k: string]: string} = {
        '=0': 'NO FEATURES',
        '=1': '1 FEATURE',
        'other': '# FEATURES'
    };

    constructor() {
    }
    ngOnChanges(changes: {[propertyName: string]: SimpleChange}) {
        this.redraw();
    }
    redraw(): void {
        this.closeRollover();

        let interpolate: any = d3.interpolateRgb(this.gradientMinColor, this.gradientMaxColor);
        let scale: any = d3.scale.linear().domain([this.gradientMinValue, this.gradientMaxValue]).range([0, 1]);

        // topFeaturesSet will contain union of top features for selected responses
        let topFeaturesSet: d3.Set = d3.set();
        // populate topFeaturesSet
        this.selectedResponses.forEach((response: string) => {
            let featureScores: FeatureScores = this.scores.scoreMap.get(response);
            featureScores.orderedFeatureIds.slice(0, this.currentNumTopFeatures).forEach((featureId: string) => {
                topFeaturesSet.add(featureId);
            });
        });

        this.topFeatureIds = topFeaturesSet.values();
        this.sortTable();

        this.rowsOfColumns =
            this.topFeatureIds.map((featureId: string) => {
                return this.selectedResponses.map((response: string) => {
                    let featureScores: FeatureScores =
                        this.scores.scoreMap.get(response);
                    let color = this.defaultColor;
                    if (featureScores.scoreMap.has(featureId)) {
                        let score = featureScores.scoreMap.get(featureId);
                        color = interpolate(scale(score));
                    }
                    return color;
                });
            });

        let maxPerRow: number[] = this.topFeatureIds.map((featureId: string) => {
            return this.scores.getMaxScoreForFeature(
                this.selectedResponses, featureId);
        });
        let maxPerColumn: number[] = this.selectedResponses.map((response: string) => {
            return this.scores.getMaxScoreForResponse(response, this.topFeatureIds);
        });
        let tableMax: number = d3.max(maxPerColumn);
        // TODO FIXME can't assume 0 is the right score
        this.rowScores = maxPerRow.map((val: number) => (isNaN(val) || tableMax == 0) ? 0 : val/tableMax);
        this.columnScores = maxPerColumn.map((val: number) => (isNaN(val) || tableMax == 0) ? 0 : val/tableMax);
    }
    sortTable(): void {
        if (this.sortRowsBy == "Alphabet") {
            this.topFeatureIds = this.topFeatureIds.sort((a: string, b: string) => {
                let n1: string = this.featureIdToNameMap.get(a);
                let n2: string = this.featureIdToNameMap.get(b);
                return d3.ascending(n1, n2);
            });
        } else if (this.sortRowsBy == "Score") {
            this.topFeatureIds = this.topFeatureIds.sort((a: string, b: string) => {
                return d3.descending(
                    this.scores.getMaxScoreForFeature(this.selectedResponses, a),
                    this.scores.getMaxScoreForFeature(this.selectedResponses, b));
            });
        } else if (this.sortRowsBy == "Similarity") {
            alert("TODO");
        } else {
            let featureScores: FeatureScores = this.scores.scoreMap.get(this.sortRowsBy);
            this.topFeatureIds = this.topFeatureIds.sort((a: string, b: string) => {
                let scoreA: number = null;
                let scoreB: number = null;
                if (featureScores.scoreMap.has(a)) {
                    scoreA = featureScores.scoreMap.get(a);
                }
                if (featureScores.scoreMap.has(b)) {
                    scoreB = featureScores.scoreMap.get(b);
                }
                return d3.descending(scoreA, scoreB);
            });
        }

        if (this.sortColumnsBy == "Alphabet") {
            // since we have an array of strings, we can use the default sort
            this.selectedResponses = this.selectedResponses.slice().sort();
        } else if (this.sortColumnsBy == "Score") {
            this.selectedResponses = this.selectedResponses.slice().sort((a: string, b: string) => {
                return d3.descending(
                    this.scores.getMaxScoreForResponse(a, this.topFeatureIds),
                    this.scores.getMaxScoreForResponse(b, this.topFeatureIds));
            });
        } else if (this.sortColumnsBy == "Similarity") {
            alert("TODO");
        } else {
            this.selectedResponses = this.selectedResponses.slice().sort((a: string, b: string) => {
                let scoreA: number = null;
                let scoreB: number = null;
                // TODO refactor; this'd be better in model
                if (this.scores.scoreMap.has(a)) {
                    let featureScores: FeatureScores = this.scores.scoreMap.get(a);
                    if (featureScores.scoreMap.has(this.sortColumnsBy)) {
                        scoreA = featureScores.scoreMap.get(this.sortColumnsBy);
                    }
                }
                if (this.scores.scoreMap.has(b)) {
                    let featureScores: FeatureScores = this.scores.scoreMap.get(b);
                    if (featureScores.scoreMap.has(this.sortColumnsBy)) {
                        scoreB = featureScores.scoreMap.get(this.sortColumnsBy);
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
        this.showRollover = true;
        this.rolloverRowIndex = selection.rowIndex;
        this.rolloverColumnIndex = selection.colIndex;
        this.hoverRowIndex = selection.rowIndex;
        this.hoverColumnIndex = selection.colIndex;

        let featureId = this.topFeatureIds[selection.rowIndex];
        let response = this.selectedResponses[selection.colIndex];
        let featureScores: FeatureScores = this.scores.scoreMap.get(response);
        if (featureScores.scoreMap.has(featureId)) {
            this.rolloverValue = featureScores.scoreMap.get(featureId);
        } else {
            this.rolloverValue = 0;
        }

        this.setRolloverCorners(selection.event);
    }
    onCellMousedOver(selection: CellHeatmapEvent) {
        if (!this.showRollover) {
            this.hoverRowIndex = selection.rowIndex;
            this.hoverColumnIndex = selection.colIndex;
        }
    }
    onSortColumnsByRow(featureId: string): void {
        this.closeRollover();
        this.sortColumnsBy = featureId;
        this.redraw();
    }
    onSortRowsByColumn(response: string): void {
        this.closeRollover();
        this.sortRowsBy = response;
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
        this.showRollover = false;
        this.rolloverRowIndex = null;
        this.rolloverColumnIndex = null;
        this.rolloverValue = null;

        this.showRowLabelContextMenu = false;
        this.rowContextMenuIndex = null;

        this.showColumnLabelContextMenu = false;
        this.columnContextMenuIndex = null;
    }
}
