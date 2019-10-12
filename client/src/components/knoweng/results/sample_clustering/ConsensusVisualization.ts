import {Component, Input, OnChanges, SimpleChange} from '@angular/core';

import {ColorGradientPicker} from '../common/ColorGradientPicker';
import {SSVState, RowStateRequest} from '../../../../models/knoweng/results/SpreadsheetVisualization';

import {HeatmapPane, MainHeatmapCellMetadata} from '../spreadsheet_visualization/HeatmapPane';
import {ColumnIndices, MainHeatmapGradientScale} from '../spreadsheet_visualization/SSVOptions';

@Component({
    moduleId: module.id,
    selector: 'consensus-visualization',
    templateUrl: './ConsensusVisualization.html',
    styleUrls: ['./ConsensusVisualization.css']
})

export class ConsensusVisualization implements OnChanges {

    @Input()
    state: SSVState;

    @Input()
    originalData: number[][];

    @Input()
    originalSampleNames: string[];

    @Input()
    fileId: number;

    @Input()
    displayedColumns: ColumnIndices;

    completeHeatmapData = [] as string[][];
    displayedHeatmapData = [] as string[][];
    sampleNameToOriginalIndex: Map<string, number>;

    // metadata
    colorScale: MainHeatmapGradientScale = null;

    constructor() { }

    ngOnChanges(changes: {[propertyName: string]: SimpleChange}) {
        if (this.state && this.state.stateRequest && this.originalData && this.originalSampleNames) {
            if (this.completeHeatmapData.length == 0) {
                this.orderAndConvertValuesToColors();
                this.subsetHeatmapDataForDisplayedColumns();
            } else {
                for (let propName in changes) {
                    if (propName == 'state') {
                        let previousRequest = changes[propName].previousValue.stateRequest;
                        let currentRequest = changes[propName].currentValue.stateRequest;
                        let isColumnOrderSame = 
                            RowStateRequest.equal(
                                previousRequest.columnGroupingRowRequest,
                                currentRequest.columnGroupingRowRequest) &&
                            RowStateRequest.equal(
                                previousRequest.columnSortingRowRequest,
                                currentRequest.columnSortingRowRequest);
                        if (!isColumnOrderSame) {
                            this.orderAndConvertValuesToColors();
                            this.subsetHeatmapDataForDisplayedColumns();
                        }
                    } else if (propName == 'displayedColumns') {
                        this.subsetHeatmapDataForDisplayedColumns();
                    }
                }
            }
        }
    }

    orderAndConvertValuesToColors(): void {
        // rebuild matrix ordered to match current column ordering
        this.sampleNameToOriginalIndex = new Map<string, number>(
            this.originalSampleNames.map((name, index) => [name, index] as [string, number])
        );
        let min = Number.POSITIVE_INFINITY;
        let max = Number.NEGATIVE_INFINITY;
        let reorderedValues = [] as number[][];
        this.state.orderedSampleNames.forEach(rowName => {
            let originalRowIndex = this.sampleNameToOriginalIndex.get(rowName);
            let row = [] as number[];
            this.state.orderedSampleNames.forEach(colName => {
                let originalColIndex = this.sampleNameToOriginalIndex.get(colName);
                let val = null;
                if (originalRowIndex !== undefined && originalColIndex !== undefined) {
                    val = this.originalData[originalRowIndex][originalColIndex];
                    if (val > max) {
                        max = val;
                    }
                    if (val < min) {
                        min = val;
                    }
                }
                row.push(val);
            });
            reorderedValues.push(row);
        });
        // TODO refactor to share some of this logic with that of SelectableRowData
        // TODO could hardcode some of this based on consensus matrix definition
        // that'd allow us to make a single pass over the values, and it'd be
        // easy to eliminate reorderedValues
        if (this.colorScale === null) {
            this.colorScale = new MainHeatmapGradientScale(min, max,
                (min < 0 && max > 0) ?
                    ColorGradientPicker.DEFAULT_TWO_COLORS_GRADIENT :
                    ColorGradientPicker.DEFAULT_ONE_COLOR_GRADIENT);
        }
        let percentScale = d3.scale.linear().domain([min, max]).range([0, 1]);
        this.completeHeatmapData = reorderedValues.map(row => {
            return row.map(cell => {
                let color = HeatmapPane.missingValueColor;
                if (cell !== null) {
                    color = this.colorScale.gradientScale(percentScale(cell));
                }
                return color;
            });
        });
    }

    //update main heatmaps when view options change
    subsetHeatmapDataForDisplayedColumns() {
        let showAllColumns = this.displayedColumns.isShowingAll();
        if (showAllColumns) {
            this.displayedHeatmapData = this.completeHeatmapData;
        } else {
            this.displayedHeatmapData = this.completeHeatmapData.map(rowVals => {
                return rowVals.slice(this.displayedColumns.startPos, this.displayedColumns.endPos + 1);
            });
        }
    }

    //In case of gradient change, we need to update colorScale and heatmap data
    updateColors(newScale: any) {
        this.colorScale.gradientScale = newScale;
        this.orderAndConvertValuesToColors();
        this.subsetHeatmapDataForDisplayedColumns();
    }

    /**
     * Given a filtered/sorted rowRank and colRank, returns metadata about the
     * cell located at the coordinates. If the heatmap is paged or expanded
     * group, the real column index is offset + colRank. The heatmap data is
     * already a sliced version of the complete heatmap data, so there is no
     * need to add the offset when looking up the color.
     */
    getCellMetadata(rowRank: number, colRank: number): MainHeatmapCellMetadata {
        if (rowRank != null && colRank != null) {
            let realColumnRank = this.displayedColumns.startPos + colRank;
            let sampleName = this.state.orderedSampleNames[realColumnRank];
            let rowName = this.state.orderedSampleNames[rowRank];
            let originalRowIndex = this.sampleNameToOriginalIndex.get(rowName);
            let originalColIndex = this.sampleNameToOriginalIndex.get(sampleName);
            let value = null as number;
            if (originalRowIndex !== undefined && originalColIndex !== undefined) {
                value = this.originalData[originalRowIndex][originalColIndex];
            }
            return new MainHeatmapCellMetadata(
                rowName, sampleName, value, this.displayedHeatmapData[rowRank][colRank]);
        }
    }
    scopedGetCellMetadata = (rr: number, cr: number) => this.getCellMetadata(rr, cr);
}
