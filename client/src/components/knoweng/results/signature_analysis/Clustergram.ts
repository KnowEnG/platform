import {Component, OnChanges, SimpleChange, Input, Output, EventEmitter} from '@angular/core';

import {SampleScores, SignatureScores} from '../../../../models/knoweng/results/SignatureAnalysis';

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
    currentNumTopSamples: number;

    @Input()
    selectedSignatures: string[];

    @Input()
    scores: SignatureScores;

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
    topSampleIds: string[] = null;

    rowScores: number[] = null;
    columnScores: number[] = null;

    /** "Alphabet" or "Score" or "Similarity" or one of the sample ids */
    sortRowsBy: string = "Score";
    /** "Alphabet" or "Score" or "Similarity" or one of the signature ids */
    sortColumnsBy: string = "Alphabet";

    signaturesCountMessageMapping: {[k: string]: string} = {
        '=0': 'NO SIGNATURES',
        '=1': '1 SIGNATURE',
        'other': '# SIGNATURES'
    };
    samplesCountMessageMapping: {[k: string]: string} = {
        '=0': 'NO SAMPLES',
        '=1': '1 SAMPLE',
        'other': '# SAMPLES'
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

        // topSamplesSet will contain union of top samples for selected signatures
        let topSamplesSet: d3.Set = d3.set();
        // populate topSamplesSet
        this.selectedSignatures.forEach((signature: string) => {
            let sampleScores: SampleScores = this.scores.scoreMap.get(signature);
            sampleScores.orderedSampleIds.slice(0, this.currentNumTopSamples).forEach((sampleId: string) => {
                topSamplesSet.add(sampleId);
            });
        });

        this.topSampleIds = topSamplesSet.values();
        this.sortTable();

        this.rowsOfColumns =
            this.topSampleIds.map((sampleId: string) => {
                return this.selectedSignatures.map((signature: string) => {
                    let sampleScores: SampleScores =
                        this.scores.scoreMap.get(signature);
                    let color = this.defaultColor;
                    if (sampleScores.scoreMap.has(sampleId)) {
                        let score = sampleScores.scoreMap.get(sampleId);
                        color = interpolate(scale(score));
                    }
                    return color;
                });
            });

        let maxPerRow: number[] = this.topSampleIds.map((sampleId: string) => {
            return this.scores.getMaxScoreForSample(
                this.selectedSignatures, sampleId);
        });
        let maxPerColumn: number[] = this.selectedSignatures.map((signature: string) => {
            return this.scores.getMaxScoreForSignature(signature, this.topSampleIds);
        });
        let tableMax: number = d3.max(maxPerColumn);
        this.rowScores = maxPerRow.map((val: number) => (isNaN(val) || tableMax == 0) ? 0 : val/tableMax);
        this.columnScores = maxPerColumn.map((val: number) => (isNaN(val) || tableMax == 0) ? 0 : val/tableMax);
    }
    sortTable(): void {
        if (this.sortRowsBy == "Alphabet") {
            this.topSampleIds = this.topSampleIds.sort((a: string, b: string) => {
                return d3.ascending(a, b);
            });
        } else if (this.sortRowsBy == "Score") {
            this.topSampleIds = this.topSampleIds.sort((a: string, b: string) => {
                return d3.descending(
                    this.scores.getMaxScoreForSample(this.selectedSignatures, a),
                    this.scores.getMaxScoreForSample(this.selectedSignatures, b));
            });
        } else if (this.sortRowsBy == "Similarity") {
            alert("TODO");
        } else {
            let sampleScores: SampleScores = this.scores.scoreMap.get(this.sortRowsBy);
            this.topSampleIds = this.topSampleIds.sort((a: string, b: string) => {
                let scoreA: number = null;
                let scoreB: number = null;
                if (sampleScores.scoreMap.has(a)) {
                    scoreA = sampleScores.scoreMap.get(a);
                }
                if (sampleScores.scoreMap.has(b)) {
                    scoreB = sampleScores.scoreMap.get(b);
                }
                return d3.descending(scoreA, scoreB);
            });
        }

        if (this.sortColumnsBy == "Alphabet") {
            // since we have an array of strings, we can use the default sort
            this.selectedSignatures = this.selectedSignatures.slice().sort();
        } else if (this.sortColumnsBy == "Score") {
            this.selectedSignatures = this.selectedSignatures.slice().sort((a: string, b: string) => {
                return d3.descending(
                    this.scores.getMaxScoreForSignature(a, this.topSampleIds),
                    this.scores.getMaxScoreForSignature(b, this.topSampleIds));
            });
        } else if (this.sortColumnsBy == "Similarity") {
            alert("TODO");
        } else {
            this.selectedSignatures = this.selectedSignatures.slice().sort((a: string, b: string) => {
                let scoreA: number = null;
                let scoreB: number = null;
                // TODO refactor; this'd be better in model
                if (this.scores.scoreMap.has(a)) {
                    let sampleScores: SampleScores = this.scores.scoreMap.get(a);
                    if (sampleScores.scoreMap.has(this.sortColumnsBy)) {
                        scoreA = sampleScores.scoreMap.get(this.sortColumnsBy);
                    }
                }
                if (this.scores.scoreMap.has(b)) {
                    let sampleScores: SampleScores = this.scores.scoreMap.get(b);
                    if (sampleScores.scoreMap.has(this.sortColumnsBy)) {
                        scoreB = sampleScores.scoreMap.get(this.sortColumnsBy);
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

        let sampleId = this.topSampleIds[selection.rowIndex];
        let signature = this.selectedSignatures[selection.colIndex];
        let sampleScores: SampleScores = this.scores.scoreMap.get(signature);
        if (sampleScores.scoreMap.has(sampleId)) {
            this.rolloverValue = sampleScores.scoreMap.get(sampleId);
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
    onSortColumnsByRow(sampleId: string): void {
        this.closeRollover();
        this.sortColumnsBy = sampleId;
        this.redraw();
    }
    onSortRowsByColumn(signature: string): void {
        this.closeRollover();
        this.sortRowsBy = signature;
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
