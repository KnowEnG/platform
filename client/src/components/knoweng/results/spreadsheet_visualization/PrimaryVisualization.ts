import {Component, Input, Output, EventEmitter, OnChanges, SimpleChange} from '@angular/core';

import {ColorGradientPicker} from '../common/ColorGradientPicker';
import {SSVState, NumericRow, Spreadsheet, SSVStateRequest, MainSpreadsheetStateRequest, RowStateRequest, SortType, FilterType} from '../../../../models/knoweng/results/SpreadsheetVisualization';

import {HeatmapPane, MainHeatmapCellMetadata} from './HeatmapPane';
import {SpreadsheetTopRowsThreshold} from './TopRowsPicker';
import {ColumnIndices, MainHeatmapGradientScale} from './SSVOptions';

@Component({
    moduleId: module.id,
    selector: 'primary-visualization',
    templateUrl: './PrimaryVisualization.html',
    styleUrls: ['./PrimaryVisualization.css']
})

export class PrimaryVisualization implements OnChanges {

    @Input()
    state: SSVState;

    @Input()
    spreadsheet: Spreadsheet;

    @Input()
    displayedColumns: ColumnIndices;

    @Output()
    settingsChanged = new EventEmitter<MainSpreadsheetStateRequest>();

    completeHeatmapData = [] as string[][];
    displayedHeatmapData = [] as string[][];

    // user settings
    sortBy: SortType = null;
    filterBy: FilterType = null;
    topRows: number = null;

    // metadata
    colorScale: MainHeatmapGradientScale = null;
    rowLabels = [] as string[];

    topRowsPickerScales = [] as number[];

    filterOptions = [
        new FilterOption(
            "Row Variance",
            FilterType.VARIANCE,
            () => false,
            "Rows are scored by variance, a statistical measure that gives a general idea of the spread of data in a row."),
        new FilterOption(
            "Correlation to Group",
            FilterType.CORRELATION_TO_GROUP,
            () => !this.state.columnGroupingRow,
            "Rows are scored by the strength of their association to the \"Group By\" row that was selected at the top " +
                "of the visualization. If no \"Group By\" row is selected, this option is not available."),
        new FilterOption(
            "Spreadsheet Order",
            FilterType.SPREADSHEET_ORDER,
            () => false,
            "Rows will be filtered according to their order of appearance in the original spreadsheet.")
    ];
    sortOptions = [
        new SortOption(
            "Row Variance",
            SortType.VARIANCE,
            () => false,
            "Rows are scored by variance, a statistical measure that gives a general idea of the spread of data in a row."),
        new SortOption(
            "Correlation to Group",
            SortType.CORRELATION_TO_GROUP,
            () => !this.state.columnGroupingRow,
            "Rows are scored by the strength of their association to the \"Group By\" row that was selected at the top " +
                "of the visualization. If no \"Group By\" row is selected, this option is not available."),
        new SortOption(
            "Spreadsheet Order",
            SortType.SPREADSHEET_ORDER,
            () => false,
            "Rows will be sorted according to their order of appearance in the original spreadsheet.")
    ];

    constructor() { }

    ngOnChanges(changes: {[propertyName: string]: SimpleChange}) {
        // cases to handle here:
        // 1. initial state arrives, before we set the default # rows, etc. -- display nothing
        // 2. second state comes through -- initialize filter, sort, rows from mssr, convert, display
        // 3. toggle on and off -- make sure it works
        // 4. displayedColumns changes -- subset
        // 5. state arrives with new sort/filter/rows for this spreadsheet -- convert, subset
        // 6. state arrives with changes that don't affect this spreadsheet -- ignore

        // don't do anything until we have a full state, a spreadsheet, and a
        // ColumnIndices instance
        if (this.state && this.state.stateRequest && this.spreadsheet && this.displayedColumns) {
            if (this.sortBy === null) {
                this.initializeSettings();
                this.updateRowLabels();
                this.convertValuesToColors();
                this.subsetHeatmapDataForDisplayedColumns();
            } else {
                for (let propName in changes) {
                    if (propName == 'state') {
                        // figure out whether the new state differs from the old
                        // w/in the scope of this spreadsheet
                        let previousState = changes[propName].previousValue;
                        let currentState = changes[propName].currentValue;
                        let sheetRequestsEqual = MainSpreadsheetStateRequest.equal(
                            this.getRequestFromState(previousState),
                            this.getRequestFromState(currentState)
                        );
                        let columnGroupingsEqual = RowStateRequest.equal(
                            previousState.stateRequest.columnGroupingRowRequest,
                            currentState.stateRequest.columnGroupingRowRequest
                        );
                        let columnSortingsEqual = RowStateRequest.equal(
                            previousState.stateRequest.columnSortingRowRequest,
                            currentState.stateRequest.columnSortingRowRequest
                        );
                        if (!sheetRequestsEqual || !columnGroupingsEqual || !columnSortingsEqual) {
                            this.updateRowLabels();
                            this.convertValuesToColors();
                            this.subsetHeatmapDataForDisplayedColumns();
                        }
                    } else if (propName == 'displayedColumns') {
                        this.subsetHeatmapDataForDisplayedColumns();
                    }
                }
            }
        }
    }

    getRequestFromState(state: SSVState): MainSpreadsheetStateRequest {
        return state.stateRequest.mainSpreadsheetStateRequests.find(mssr => {
            return mssr.spreadsheetId == this.spreadsheet.spreadsheetId;
        });
    }

    initializeSettings(): void {
        // we're displaying this data for the first time
        // initialize our component state from the visualization state
        let mssr = this.getRequestFromState(this.state);
        this.sortBy = mssr.sortType;
        this.filterBy = mssr.filterType;
        this.topRows = mssr.filterLimit;
        let defaultScales = [20, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000];
        let maxRows = this.spreadsheet.rowNames.length;
        this.topRowsPickerScales = defaultScales.filter(num => num <= maxRows);
        // there are two circumstances--both common--under which we now want to
        // add the value of maxRows as a scale option:
        // - maxRows is less than the smallest default
        // - maxRows is larger than the largest filtered default
        if (this.topRowsPickerScales.length == 0 ||
                maxRows > this.topRowsPickerScales[this.topRowsPickerScales.length - 1]) {
            this.topRowsPickerScales.push(maxRows);
        }
    }

    updateRowLabels(): void {
        this.rowLabels = this.spreadsheet.filteredAndSortedRows.map(row => row.getName());
    }

    convertValuesToColors(): void {
        let rows: NumericRow[] = this.spreadsheet.filteredAndSortedRows;
        // TODO refactor to share some of this logic with that of SelectableRowData
        let min = d3.min(rows, (row: NumericRow) => row.getMin());
        let max = d3.max(rows, (row: NumericRow) => row.getMax());
        if (this.colorScale === null) {
            this.colorScale = new MainHeatmapGradientScale(min, max,
                (min < 0 && max > 0) ?
                    ColorGradientPicker.DEFAULT_TWO_COLORS_GRADIENT :
                    ColorGradientPicker.DEFAULT_ONE_COLOR_GRADIENT);
        }
        let rawData = rows.map(row => row.getValuesOrderedBySampleNames());
        let percentScale = d3.scale.linear().domain([min, max]).range([0, 1]);
        this.completeHeatmapData = rawData.map((row: number[]) => {
            return row.map((cell: number) => {
                let color = HeatmapPane.missingValueColor;
                if (cell !== null) {
                    color = this.colorScale.gradientScale(percentScale(cell));
                }
                return color;
            });
        });
    }

    sortByChanged(sortIndex: number): void {
        this.emitStateRequest();
    }

    filterByChanged(filterIndex: number): void {
        this.emitStateRequest();
    }

    topRowsChanged(threshold: SpreadsheetTopRowsThreshold) {
        this.topRows = threshold.topRowsThreshold;
        this.emitStateRequest();
    }

    emitStateRequest(): void {
        let mssr = new MainSpreadsheetStateRequest(
            this.spreadsheet.spreadsheetId, this.filterBy, this.topRows, this.sortBy);
        this.settingsChanged.emit(mssr);
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
        this.convertValuesToColors();
        this.subsetHeatmapDataForDisplayedColumns();
    }

    /**
     * This gives a general idea of the portion of missing values in a spreadsheet. If the return percentage is <0.01%, it means the spreadsheet has very few missing values.
     * For some spreadsheets that were loaded in old days, this information is not available, e.g. NA
     */
    getTotalPercentMissingValues(): string {
        let columnCount = this.spreadsheet.sampleNames.length;
        let rowCount = this.spreadsheet.rowNames.length;
        let size = columnCount * rowCount;
        if (this.spreadsheet.rowNanCounts) {
            let totalNanCount = this.spreadsheet.rowNanCounts.reduce((a, b) => a + b, 0);
            let percent = (totalNanCount / size * 100)
            return percent < 0.01 ? "<0.01%" : percent.toFixed(2) + "%";
        } else {
            return "NA";
        }
    }

    getTotalRowsWithMissingValues(): number {
        return this.spreadsheet.rowNanCounts.filter(count => count > 0).length;
    }

    getTotalColumnsWithMissingValues(): number {
        return this.spreadsheet.columnNanCounts.filter(count => count > 0).length;
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
            let row = this.spreadsheet.filteredAndSortedRows[rowRank];
            let value = row.getValuesOrderedBySampleNames()[realColumnRank];
            let rowIndex = row.idx;
            let rowName = row.getName();
            let colIndex = this.spreadsheet.orderedSampleIndices[realColumnRank];
            let sampleName = this.state.orderedSampleNames[realColumnRank];
            return new MainHeatmapCellMetadata(
                rowName, sampleName, value, this.displayedHeatmapData[rowRank][colRank]);
        }
    }
    scopedGetCellMetadata = (rr: number, cr: number) => this.getCellMetadata(rr, cr);
}

class FilterOption {
    constructor(
        public label: string,
        public value: FilterType,
        public isDisabled: () => boolean,
        public description: string) { }
}
class SortOption {
    constructor(
        public label: string,
        public value: SortType,
        public isDisabled: () => boolean,
        public description: string) { }
}