import {Component, Input, Output, EventEmitter} from '@angular/core';

import {Job} from '../../../../models/knoweng/Job';
import {SSVState, Spreadsheet} from '../../../../models/knoweng/results/SpreadsheetVisualization';
import {LogService} from '../../../../services/common/LogService';

import {SelectableRowData} from './SelectableTypes';

/**
 * This is a reusable Row Selector for the Spreadsheet Visualizer view.
 *   Inputs:
 *      - multiSelect: false => if true, present checkboxes instead of radio buttons
 *      - types: 'all' => the type(s) of spreadsheet rows to present
 *      - showScores: true => show the "score" column?
 */


@Component({
    moduleId: module.id,
    selector: 'row-selector',
    templateUrl: './RowSelector.html',
    styleUrls: ['./RowSelector.css']
})

export class RowSelector {
    class = 'relative';

    @Input()
    job: Job;

    @Input()
    state: SSVState;
    
    @Input()
    multiSelect: boolean = false;
    
    @Input()
    // 'categoric', 'numeric', 'other', 'numeric,categoric', 'all', etc
    types: string = 'all';
    
    @Input()
    showScores: boolean = true;
    
    @Output()
    selectionChanged: EventEmitter<SelectableRowData[]> = new EventEmitter<SelectableRowData[]>();

    showPanel: boolean = false;
    selectedFile: Spreadsheet = null;
    selection: SelectableRowData[] = [];
    
    pageNum: number = 0;
    rowOptionThreshold: number = 15;
    
    rowOptions: SelectableRowData[] = [];
    rowSearchResults: SelectableRowData[] = [];
    currentFilter: string = '';
    
    constructor(public logger: LogService) {
    }
    
    toggleShowPanel($event: MouseEvent): void {
        $event.preventDefault();
        $event.stopPropagation();
        this.showPanel = !this.showPanel;
    }
    
    showPanelChanged(value: boolean): void {
        this.showPanel = false;
    }
    
    /**
     * Select a new file, clearing out per-file settings and resetting search results
     */
    selectFile(spreadsheet: Spreadsheet) {
        // Reset to first page when file selection changes
        this.pageNum = 0;
        this.currentFilter = '';
        
        // Calculate numberOfPages for current spreadsheet
        this.selectedFile = spreadsheet;
        
        // Populate rowOptions with all relevant rows (assume empty filter)
        this.rowOptions = this.getRowOptions(this.selectedFile);
        
        if (this.rowOptions.length > this.rowOptionThreshold) {
            this.rowSearchResults = [];
        } else {
            this.rowSearchResults = this.rowOptions;
        }
    }

    isSelected(row: SelectableRowData): boolean {
        return row.selected;
    }
    
    /** 
     * When a user selects a row from the typeahead, add it 
     * to our list of search results 
     */
    addRowToSearchResults(event: any) {
        let targetRowName = event.item;
        let targetRow = this.rowOptions.find(row => row.getName() === targetRowName);
        if (targetRow) {
            this.rowSearchResults.push(targetRow);
        }
    }
    
    /**
     * When multiSelect == false: marks the current row as selected (always)
     * When multiSelect == true:  toggles selection of the current row
     */
    select(row: SelectableRowData): void {
        if (this.multiSelect) {
            let index = this.selection.indexOf(row);
            
            // If item is not selected, select it
            if (index === -1) {
                row.selected = true;
                this.selection.push(row);
            } else {
                this.selection[index].selected = false;
                
                // Otherwise, de-select
                this.selection.splice(index, 1);
            }
        } else {
            // De-select previous value;
            let previous = this.selection[0];
            if (previous) {
                previous.selected = false;
            }
            
            // Replace selection with chosen value
            row.selected = true;
            this.selection = [row];
        }
        
        this.selectionChanged.emit(this.selection);
    }
    
    /** 
     * Counts the number of selected rows from the given spreadsheet 
     * (NOTE: this is always 1 or 0, unless multi-select is true )
     */
    getSelectedRowsCount(spreadsheet: Spreadsheet): number {
        if (!this.selection) {
            return 0;
        }
        
        let matches = this.selection.filter(row => row.spreadsheet.spreadsheetId === spreadsheet.spreadsheetId);
        return matches.length;
    }
    
    /** 
     * Returns true if the specified row matches the given "types"
     */
    isRelevantRow(spreadsheet: Spreadsheet, rowIdx: number, checkFilter: boolean = false): boolean {
        let rowType = spreadsheet.rowTypes[rowIdx];
        let rowName = spreadsheet.rowNames[rowIdx];
        
        if (this.types !== 'all' && this.types.split(',').indexOf(rowType) === -1) {
            return false;
        }
        
        let containsFilter = rowName.indexOf(this.currentFilter);
        
        // If row matches our current search filter AND desired type, return true
        return !checkFilter || !this.currentFilter || containsFilter !== -1;
    }
    
    /** 
     * Returns the number of rows matching the specified "types"
     */
    getNumberOfRelevantRows(spreadsheet: Spreadsheet, checkFilter: boolean = false) {
        // Create an array of numbers from 0 to numRows
        let indices = Array.from(Array(spreadsheet.rowNames.length).keys());
        let relevantRowIdxs = indices.filter(rowIdx => this.isRelevantRow(spreadsheet, rowIdx, checkFilter));
        return relevantRowIdxs.length;
    }
    
    /** 
     * Returns all spreadsheet with at least one row matching the given "types"
     */
    getRelevantSpreadsheets(checkFilter: boolean = false): Spreadsheet[] {
        let spreadsheets: Spreadsheet[] = [];
        this.state.spreadsheets.forEach(spreadsheet => {
            let relevantRows = this.getNumberOfRelevantRows(spreadsheet, checkFilter);
            if (relevantRows > 0) {
                spreadsheets.push(spreadsheet);
            }
        });
        return spreadsheets;
    }
    
    /** 
     * Given an arbitrary field name, returns a function that will 
     * sort arbitrary objects by the given field 
     */
    sortByField(fieldName: string) {
        return (a: any, b: any) => {
            if (a[fieldName] < b[fieldName]) {
                return 1;
            } else if (a[fieldName] > b[fieldName]) {
                return -1;
            } else {
                return 0;
            }
        };
    }
    
    /** 
     * Returns the list of relevant row options for the current spreadsheet / page
     */
    getRowOptions(spreadsheet: Spreadsheet) {
        if (!spreadsheet) {
            return [];
        }
        
        // Accumulate rows from the current page
        // This loop assumes that the loop index matches the offset into the spreadsheet
        let rowOptions: SelectableRowData[] = [];
        let existingSelectionsForSpreadsheet = this.selection.filter((srd) => {
            return srd.spreadsheet.spreadsheetId == spreadsheet.spreadsheetId;
        });
        for (let rowIdx = 0; rowIdx < spreadsheet.rowNames.length; rowIdx++) {
            if (!this.isRelevantRow(spreadsheet, rowIdx, true)) {
                // Increment pageEnd to keep the same number of items on each full page
                continue;
            }
            
            // need to preserve selected state if this row was previously selected
            let existingOption = existingSelectionsForSpreadsheet.find((srd) => {
                return srd.rowIdx == rowIdx;
            });
            if (existingOption) {
                rowOptions.push(existingOption);
            } else {
                let newOption = new SelectableRowData(false, spreadsheet, rowIdx);
                rowOptions.push(newOption);
            }
        }
        
        // FIXME: Sort by score before returning?
        return rowOptions.sort(this.showScores ? this.sortByField('score') : this.sortByField('name'));
    }

    /**
     * Returns true iff the host set `showScores` AND scores are loaded. In
     * practice this translates to "picking something besides the column
     * grouping AND the column grouping has already been picked."
     */
    isShowingScores(): boolean {
        return this.showScores && this.state.spreadsheets.some((spreadsheet) => spreadsheet.rowCorrelations.length > 0);
    }
}
