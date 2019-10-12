import {Component, OnInit, OnChanges, Input, SimpleChange} from '@angular/core';

import {SelectablePrimarySpreadsheet} from '../spreadsheet_visualization/SelectableTypes';
import {ColumnIndices, ExpandedGroup} from '../spreadsheet_visualization/SSVOptions';
import {Job} from '../../../../models/knoweng/Job';
import {Result} from '../../../../models/knoweng/results/SampleClustering';
import {SSVState, Spreadsheet, MainSpreadsheetStateRequest, FilterType, SortType, RowStateRequest, SSVStateRequest} from '../../../../models/knoweng/results/SpreadsheetVisualization';

import {SpreadsheetVisualizationService} from '../../../../services/knoweng/SpreadsheetVisualizationService';

@Component({
    moduleId: module.id,
    selector: 'sc-data-area',
    templateUrl: './DataArea.html',
    styleUrls: ['./DataArea.css']
})

export class DataArea implements OnInit, OnChanges {
    class = 'relative';

     //This is mainly used to calculate initial number of rows to fetch, the design has 476px, minus 20 to accomondate file name label
    static readonly MAIN_HEATMAP_AREA_HEIGHT: number = 456;

    @Input()
    job: Job;

    @Input()
    state: SSVState;

    @Input()
    result: Result;

    selectablePrimarySpreadsheets = [] as SelectablePrimarySpreadsheet[];
    primarySpreadsheets = [] as Spreadsheet[];
    displayConsensusMatrix = false;

    //included here are options to control views (the start and end column postions of current view) and options to control how row data appears (filter, sort and top rows)
    displayedColumns: ColumnIndices;
    expandedGroup: ExpandedGroup = null;

    /** one of visualizations, spreadsheet, job */
    activeTab: string = 'visualizations';

    constructor(private _ssvService: SpreadsheetVisualizationService) { }

    ngOnInit() {
       // Build primary / mini heatmap data in primary/secondary heatmap component
    }

    ngOnChanges(changes: {[propertyName: string]: SimpleChange}) {
        // note that this condition differs slightly from what exists in SSV's DataArea.ngOnChanges
        // that's because SSV needs to handle the case of no primary spreadsheets
        // we'll always have primary spreadsheets in SC
        if (this.state && this.result && this.selectablePrimarySpreadsheets.length == 0) {
            let groupingSpreadsheetId = null;
            let sortingSpreadsheetId = null;
            this.state.spreadsheets.forEach(ss => {
                if (ss.fileId == this.result.initialColumnGroupingFileId) {
                    groupingSpreadsheetId = ss.spreadsheetId;
                } else if (ss.fileId == this.result.initialColumnSortingFileId) {
                    sortingSpreadsheetId = ss.spreadsheetId;
                } else if (ss.isEligibleForMainHeatmap()) {
                    this.selectablePrimarySpreadsheets.push(
                        new SelectablePrimarySpreadsheet(true, ss.fileId)
                    );
                }
            });
            if (this.result.consensusMatrixFileId) {
                this.selectablePrimarySpreadsheets.push(
                    new SelectablePrimarySpreadsheet(true, this.result.consensusMatrixFileId)
                );
            }
            this.refreshPrimarySpreadsheets();
            this.refreshDisplayedColumns();
            let rowLimit = Math.round(DataArea.MAIN_HEATMAP_AREA_HEIGHT / (10 * this.primarySpreadsheets.length));
            let mainSpreadsheetStateRequests: MainSpreadsheetStateRequest[] = this.primarySpreadsheets.map(ss => {
                return new MainSpreadsheetStateRequest(
                    ss.spreadsheetId,
                    FilterType.CORRELATION_TO_GROUP,
                    Math.min(rowLimit, ss.rowNames.length),
                    SortType.CORRELATION_TO_GROUP
                );
            });
            //should be the first time to load row data
            let groupingRequest = new RowStateRequest(
                groupingSpreadsheetId, this.result.initialColumnGroupingFeatureIndex);
            let sortingRequest = new RowStateRequest(
                sortingSpreadsheetId, this.result.initialColumnSortingFeatureIndex);
            let stateRequest = new SSVStateRequest(
                groupingRequest, sortingRequest, mainSpreadsheetStateRequests, [], null, null, null, [], null);
            this._ssvService.updateSSVState(stateRequest)
        }
    }

    refreshDisplayedColumns(): void {
        let totalColumnCount = this.state.orderedSampleNames.length;
        if (this.expandedGroup) {
            this.displayedColumns = new ColumnIndices(
                this.expandedGroup.groupStartColumnPos,
                this.expandedGroup.groupEndColumnPos,
                totalColumnCount);
        } else {
            this.displayedColumns = new ColumnIndices(0, totalColumnCount - 1, totalColumnCount);
        }
    }

    refreshPrimarySpreadsheets(): void {
        let selectedFileIds = this.selectablePrimarySpreadsheets
            .filter(sps => sps.selected)
            .map(sps => sps.fileId);
        let selectedFileIdSet = new Set<number>(selectedFileIds);
        this.primarySpreadsheets = this.state.spreadsheets.filter(ss => selectedFileIdSet.has(ss.fileId));
        this.displayConsensusMatrix = selectedFileIdSet.has(this.result.consensusMatrixFileId);
    }

    /**
     * Update spreadsheet array to pass into PrimaryVisualization
     **/
    handleSpreadsheetToggle(toggledSps: SelectablePrimarySpreadsheet) {
        // clone old arrays so anyone holding a reference doesn't find their data
        // mutated
        this.selectablePrimarySpreadsheets = this.selectablePrimarySpreadsheets.map(sps => {
            let returnVal = sps;
            if (toggledSps.fileId == sps.fileId) {
                returnVal = new SelectablePrimarySpreadsheet(!sps.selected, sps.fileId);
            }
            return returnVal;
        });
        this.refreshPrimarySpreadsheets();
    }

    /**
     * Update ExpandedGroup object to pass into ColumnOptionsComponent
     **/
    handleExpandedGroupChange(expandedGroup: ExpandedGroup) {
        this.expandedGroup = expandedGroup;
        this.refreshDisplayedColumns();
    }

    /**
     * Update the first and last displayable columns' indices so we could adjust all the heatmaps, which include
     * column grouping and/or sorting single row heatmap(s), primary heatmap and any secondary single row heatmap(s).
     **/
    handleDisplayedColumnsChange(newColumns: ColumnIndices) {
        this.displayedColumns = newColumns;
    }

    handlePrimaryVisualizationSettingsChange(newMssr: MainSpreadsheetStateRequest): void {
        let stateRequest = this.state.stateRequest.copy();
        stateRequest.mainSpreadsheetStateRequests = stateRequest.mainSpreadsheetStateRequests.map(mssr => {
            let returnVal = mssr;
            if (mssr.spreadsheetId == newMssr.spreadsheetId) {
                returnVal = newMssr;
            }
            return returnVal;
        });
        this._ssvService.updateSSVState(stateRequest)
    }

    isGroupingByCluster(): boolean {
        let returnVal = false;
        if (this.state.columnGroupingRow) {
            let gRow = this.state.columnGroupingRow;
            returnVal =
                gRow.idx == this.result.initialColumnGroupingFeatureIndex &&
                gRow.spreadsheet.fileId == this.result.initialColumnGroupingFileId;
        }
        return returnVal;
    }
}
