import {Component, OnInit, OnChanges, Input, SimpleChange} from '@angular/core';

import {SelectablePrimarySpreadsheet} from './SelectableTypes';
import {ColumnIndices, ExpandedGroup} from './SSVOptions';
import {Job} from '../../../../models/knoweng/Job';
import {SSVState, Spreadsheet, MainSpreadsheetStateRequest, FilterType, SortType, SSVStateRequest} from '../../../../models/knoweng/results/SpreadsheetVisualization';

import {SpreadsheetVisualizationService} from '../../../../services/knoweng/SpreadsheetVisualizationService';

@Component({
    moduleId: module.id,
    selector: 'ss-data-area',
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

    selectablePrimarySpreadsheets = [] as SelectablePrimarySpreadsheet[];
    primarySpreadsheets = [] as Spreadsheet[];

    // included here are options to control views (the start and end column postions of current view)
    // and options to control how row data appears (filter, sort and top rows)
    displayedColumns: ColumnIndices;
    expandedGroup: ExpandedGroup = null;

    /** one of visualizations, spreadsheet, job */
    activeTab: string = 'visualizations';

    isRowDataRequested = false;

    constructor(private _ssvService: SpreadsheetVisualizationService) { }

    ngOnInit() {
       // Build primary / mini heatmap data in primary/secondary heatmap component
    }

    ngOnChanges(changes: {[propertyName: string]: SimpleChange}) {
        if (this.state != undefined) {
            for (let propName in changes) {
                // note we need isRowDataRequested instead of just checking selectablePrimarySpreadsheets.length
                // because SSV allows the user to configure a run without any primary spreadsheets
                if (propName == 'state' && !this.isRowDataRequested) {
                    this.selectablePrimarySpreadsheets = this.state.spreadsheets
                        .filter(ss => ss.isEligibleForMainHeatmap())
                        .map(ss => new SelectablePrimarySpreadsheet(true, ss.fileId));
                    this.refreshPrimarySpreadsheets();
                    this.refreshDisplayedColumns();
                    let rowLimit = Math.round(DataArea.MAIN_HEATMAP_AREA_HEIGHT / (10 * this.primarySpreadsheets.length));
                    let mainSpreadsheetStateRequests = this.primarySpreadsheets.map(ss => {
                        return new MainSpreadsheetStateRequest(
                            ss.spreadsheetId,
                            FilterType.VARIANCE,
                            Math.min(rowLimit, ss.rowNames.length),
                            SortType.VARIANCE
                        );
                    });
                    //should be the first time to load row data
                    let stateRequest = new SSVStateRequest(
                        null, null, mainSpreadsheetStateRequests, [], null, null, null, [], null);
                    this._ssvService.updateSSVState(stateRequest)
                    this.isRowDataRequested = true;
                }
            }
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
}

