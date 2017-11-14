import {Component, OnChanges, SimpleChange, Input, Output, EventEmitter} from '@angular/core';

import {GeneScores, ResponseScores} from '../../../../models/knoweng/results/GenePrioritization';

import {hexToDec, CellHeatmapEvent} from '../common/CellHeatmap';

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
    currentNumTopGenes: number;

    @Input()
    selectedResponses: string[];

    @Input()
    scores: ResponseScores;

    @Input()
    geneIdToNameMap: d3.Map<string>;

    defaultColor: number = 0xEEEEEE; // 0x607?

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

    rowsOfColumns: number[][] = null;
    topGeneIds: string[] = null;

    rowScores: number[] = null;
    columnScores: number[] = null;

    /** "Alphabet" or "Score" or "Similarity" or one of the gene ids */
    sortRowsBy: string = "Score";
    /** "Alphabet" or "Score" or "Similarity" or one of the comparison gene set names */
    sortColumnsBy: string = "Alphabet";

    /** create instance method on our class so we can use it in template */
    hexToDec = hexToDec;

    responsesCountMessageMapping: {[k: string]: string} = {
        '=0': 'NO RESPONSES',
        '=1': '1 RESPONSE',
        'other': '# RESPONSES'
    };
    genesCountMessageMapping: {[k: string]: string} = {
        '=0': 'NO GENES',
        '=1': '1 GENE',
        'other': '# GENES'
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

        // topGenesSet will contain union of top genes for selected responses
        let topGenesSet: d3.Set = d3.set();
        // populate topGenesSet
        this.selectedResponses.forEach((response: string) => {
            let geneScores: GeneScores = this.scores.scoreMap.get(response);
            geneScores.orderedGeneIds.slice(0, this.currentNumTopGenes).forEach((geneId: string) => {
                topGenesSet.add(geneId);
            });
        });

        this.topGeneIds = topGenesSet.values();
        this.sortTable();

        this.rowsOfColumns =
            this.topGeneIds.map((geneId: string) => {
                return this.selectedResponses.map((response: string) => {
                    let geneScores: GeneScores =
                        this.scores.scoreMap.get(response);
                    var color: number = this.defaultColor;
                    if (geneScores.scoreMap.has(geneId)) {
                        let score: number = geneScores.scoreMap.get(geneId);
                        color = this.hexToDec(interpolate(scale(score)));
                    }
                    return color;
                });
            });

        let maxPerRow: number[] = this.topGeneIds.map((geneId: string) => {
            return this.scores.getMaxScoreForGene(
                this.selectedResponses, geneId);
        });
        let maxPerColumn: number[] = this.selectedResponses.map((response: string) => {
            return this.scores.getMaxScoreForResponse(response, this.topGeneIds);
        });
        let tableMax: number = d3.max(maxPerColumn);
        // TODO FIXME can't assume 0 is the right score
        this.rowScores = maxPerRow.map((val: number) => (isNaN(val) || tableMax == 0) ? 0 : val/tableMax);
        this.columnScores = maxPerColumn.map((val: number) => (isNaN(val) || tableMax == 0) ? 0 : val/tableMax);
    }
    sortTable(): void {
        if (this.sortRowsBy == "Alphabet") {
            this.topGeneIds = this.topGeneIds.sort((a: string, b: string) => {
                let n1: string = this.geneIdToNameMap.get(a);
                let n2: string = this.geneIdToNameMap.get(b);
                return d3.ascending(n1, n2);
            });
        } else if (this.sortRowsBy == "Score") {
            this.topGeneIds = this.topGeneIds.sort((a: string, b: string) => {
                return d3.descending(
                    this.scores.getMaxScoreForGene(this.selectedResponses, a),
                    this.scores.getMaxScoreForGene(this.selectedResponses, b));
            });
        } else if (this.sortRowsBy == "Similarity") {
            alert("TODO");
        } else {
            let geneScores: GeneScores = this.scores.scoreMap.get(this.sortRowsBy);
            this.topGeneIds = this.topGeneIds.sort((a: string, b: string) => {
                let scoreA: number = null;
                let scoreB: number = null;
                if (geneScores.scoreMap.has(a)) {
                    scoreA = geneScores.scoreMap.get(a);
                }
                if (geneScores.scoreMap.has(b)) {
                    scoreB = geneScores.scoreMap.get(b);
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
                    this.scores.getMaxScoreForResponse(a, this.topGeneIds),
                    this.scores.getMaxScoreForResponse(b, this.topGeneIds));
            });
        } else if (this.sortColumnsBy == "Similarity") {
            alert("TODO");
        } else {
            this.selectedResponses = this.selectedResponses.slice().sort((a: string, b: string) => {
                let scoreA: number = null;
                let scoreB: number = null;
                // TODO refactor; this'd be better in model
                if (this.scores.scoreMap.has(a)) {
                    let geneScores: GeneScores = this.scores.scoreMap.get(a);
                    if (geneScores.scoreMap.has(this.sortColumnsBy)) {
                        scoreA = geneScores.scoreMap.get(this.sortColumnsBy);
                    }
                }
                if (this.scores.scoreMap.has(b)) {
                    let geneScores: GeneScores = this.scores.scoreMap.get(b);
                    if (geneScores.scoreMap.has(this.sortColumnsBy)) {
                        scoreB = geneScores.scoreMap.get(this.sortColumnsBy);
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

        let geneId = this.topGeneIds[selection.rowIndex];
        let response = this.selectedResponses[selection.colIndex];
        let geneScores: GeneScores = this.scores.scoreMap.get(response);
        if (geneScores.scoreMap.has(geneId)) {
            this.rolloverValue = geneScores.scoreMap.get(geneId);
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
    onSortColumnsByRow(geneId: string): void {
        this.closeRollover();
        this.sortColumnsBy = geneId;
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
