import {Component, OnInit, OnChanges, Input, Output, EventEmitter, SimpleChange} from '@angular/core';

import {Job} from '../../../../models/knoweng/Job';
import {SSVState, CategoricRow, Row, SSVStateRequest, RowStateRequest} from '../../../../models/knoweng/results/SpreadsheetVisualization';
import {SelectableRowData} from './SelectableTypes';
import {ExpandedGroup, ColumnIndices} from './SSVOptions';
import {SpreadsheetVisualizationService} from '../../../../services/knoweng/SpreadsheetVisualizationService';

@Component({
    moduleId: module.id,
    selector: 'column-options',
    templateUrl: './ColumnOptionsComponent.html',
    styleUrls: ['./ColumnOptionsComponent.css']
})

/**
 * This is where user gets to choose a column so samples will be grouped by this column, and/or to choose a column so
 * samples can be sorted by this column. In turn, the heatmaps will be changed.
 * 
 * NOTE: maybe I should rename the component name to reflect the above, essentially this is to rearrange sample ids
 **/
export class ColumnOptionsComponent implements OnInit, OnChanges {
    //designed column heatmap width
    static readonly HEATMAP_WIDTH = 750;
    
    @Input()
    job: Job;

    @Input()
    state: SSVState;

    //Expand a group by clicking the group title area to highlight, then click the "expand" icon
    @Input()
    expandedGroup: ExpandedGroup;
    
    @Input()
    displayedColumns: ColumnIndices;
    
    @Output()
    expandedGroupChanged: EventEmitter<ExpandedGroup> = new EventEmitter<ExpandedGroup> ();
    
    columnGroups: any[] = [];
    groupColumnsBy: SelectableRowData = null;
    displayedGroupColumnsHeatmapData: string[] = [];
    sortColumnsBy: SelectableRowData = null;
    displayedSortColumnsHeatmapData: string[] = [];
    
    constructor(private _ssvService: SpreadsheetVisualizationService) {}
    
    ngOnInit() {
    }
    
    ngOnChanges(changes: {[propertyName: string]: SimpleChange}) {
        for (let propName in changes) {
            if (propName == 'state') {
                let previousState = changes[propName].previousValue;
                let currentState = changes[propName].currentValue;
                // TODO: Null checks
                if (previousState && currentState) {
                    // handle case where initial grouping and sorting set by ancenstor component
                    if (!this.groupColumnsBy && currentState.columnGroupingRow) {
                        this.groupColumnsBy = new SelectableRowData(
                            true,
                            currentState.columnGroupingRow.spreadsheet,
                            currentState.columnGroupingRow.idx
                        );
                    }
                    if (!this.sortColumnsBy && currentState.columnSortingRow) {
                        this.sortColumnsBy = new SelectableRowData(
                            true,
                            currentState.columnSortingRow.spreadsheet,
                            currentState.columnSortingRow.idx
                        );
                    }
                    // Regroup if groupColumnsBy changed
                    if (previousState.columnGroupingRow !== currentState.columnGroupingRow) {
                        this.regroupColumns(currentState.columnGroupingRow);
                    }
                    // Resort if sortColumnsBy changed
                    if (previousState.columnSortingRow !== currentState.columnSortingRow) {
                        this.resortColumns(currentState.columnSortingRow);
                    }
                } else {
                    // Group and sort columns
                    this.regroupColumns(currentState.columnGroupingRow);
                    this.resortColumns(currentState.columnSortingRow);
                }
            } else if (propName == 'expandedGroup') {
                this.updateGroupColumnsHeatmap();
                this.updateSortColumnsHeatmap();
            } else if (propName == 'displayedColumns') {
                let previous: ColumnIndices = changes[propName].previousValue;
                let current: ColumnIndices = changes[propName].currentValue;
                if (!ColumnIndices.equal(previous, current)) {
                    this.createGroupsInCurrentView(this.state.columnGroupingRow);
                    this.updateGroupColumnsHeatmap();
                    this.updateSortColumnsHeatmap();
                }
            }
        }
    }
    
    regroupColumns(groupColumnsBy: CategoricRow): void {
        if (!groupColumnsBy || groupColumnsBy.getType() !== 'categoric') {
            this.columnGroups = [];
            
            return;
        }
        // Repopulate <cell-heatmap> for groupColumnsBy
        this.groupColumnsBy.updateData();
        this.createGroupsInCurrentView(groupColumnsBy);
        this.updateGroupColumnsHeatmap();
        // Re-sort after grouping changes
        this.resortColumns(this.state.columnSortingRow);
    }
    
    createGroupsInCurrentView(groupColumnsBy: CategoricRow) {
        if(groupColumnsBy) {
            let colorScale = this.groupColumnsBy.getColorScale() as d3.scale.Ordinal<string, {}>;
            let uniqueValues = groupColumnsBy.getDistinctValues();
            let orderedSamples = groupColumnsBy.getValuesOrderedBySampleNames();
            
            // Loop over all groups to build up group header metadata
            this.columnGroups = [];
            let groupStartColumnPos = this.displayedColumns.startPos;
            let groupEndColumnPos = 0; 
            uniqueValues.forEach(value => {
                let displayedSamples = orderedSamples.slice(this.displayedColumns.startPos, this.displayedColumns.endPos + 1);
                let size = displayedSamples.filter(item => item == value).length;
                if (size > 0) {
                    let shortName = value === null ? "not specified" : "" + value;
                    let rowIdx = groupColumnsBy.idx;
                    groupEndColumnPos = groupStartColumnPos + size - 1;
                    let spreadsheetId = groupColumnsBy.spreadsheet.spreadsheetId;
                    
                    // TODO: This is probably not the right place for this to live...
                    let total = displayedSamples.length;
                    
                    // Grab the next color from our color range
                    let color = colorScale(value);
                    
                    // in chrome, fractional widths not handled well; TODO revisit
                    let width = size / total * ColumnOptionsComponent.HEATMAP_WIDTH;
                    
                    let highlighted = false;
                    
                    let expanded = false;
                    
                    let group = { shortName, size, rowIdx, spreadsheetId, total, color, width, highlighted, expanded, groupStartColumnPos, groupEndColumnPos};
                    this.columnGroups.push(group);
                    groupStartColumnPos = groupEndColumnPos + 1;
                }
            });
        }
    }
    
    //update "Group columns by" mini-heatmap when view options change
    updateGroupColumnsHeatmap() {
        if (this.groupColumnsBy) {
            let completeGroupColumnsHeatmapData = this.groupColumnsBy.getColorRGBValues();
            if (this.displayedColumns.isShowingAll()) {
                this.displayedGroupColumnsHeatmapData = completeGroupColumnsHeatmapData;
            } else {
                this.displayedGroupColumnsHeatmapData = completeGroupColumnsHeatmapData.slice(
                    this.displayedColumns.startPos, this.displayedColumns.endPos + 1);
            }
        }
    }
    
    //update "Sort columns by" mini-heatmap when view options change
    updateSortColumnsHeatmap() {
        if (this.sortColumnsBy) {
            let completeSortColumnsHeatmapData = this.sortColumnsBy.getColorRGBValues();
            if (this.displayedColumns.isShowingAll()) {
                this.displayedSortColumnsHeatmapData = completeSortColumnsHeatmapData;
            } else { 
                this.displayedSortColumnsHeatmapData = completeSortColumnsHeatmapData.slice(
                    this.displayedColumns.startPos, this.displayedColumns.endPos + 1);
            }
        }
    }
    
    resortColumns(sortColumnsBy: Row): void {
        if (!sortColumnsBy) {
            return;
        }
        this.sortColumnsBy.updateData();
        this.updateSortColumnsHeatmap();
    }
    
    selectGroupColumnsBy(rows: SelectableRowData[]): void {
        if (rows && rows.length) {
            this.groupColumnsBy = rows[0];
            this.updateState();
        } else {
            this.groupColumnsBy = null;
        }
    }
    
    updateState(): void {
        let groupColumnsByRowRequest: RowStateRequest = null;
        if (this.groupColumnsBy) {
            groupColumnsByRowRequest = new RowStateRequest(this.groupColumnsBy.spreadsheet.spreadsheetId, this.groupColumnsBy.rowIdx);
        }
        
        // note: if user hasn't designated a basis for column sorting, just pass null
        // service will use column grouping, if not null, or else arbitrary sort
        let sortColumnsByRowRequest: RowStateRequest = null;
        if (this.sortColumnsBy) {
             sortColumnsByRowRequest = new RowStateRequest(this.sortColumnsBy.spreadsheet.spreadsheetId, this.sortColumnsBy.rowIdx);
         }
        
        let request = new SSVStateRequest(
            groupColumnsByRowRequest, 
            sortColumnsByRowRequest, 
            this.state.stateRequest.mainSpreadsheetStateRequests,
            this.state.stateRequest.otherRowStateRequests,
            this.state.stateRequest.timeToEventEventRowRequest,
            this.state.stateRequest.timeToEventTimeRowRequest,
            this.state.stateRequest.timeToEventEventValue,
            this.state.stateRequest.timeToEventPvalRequests,
            null);
        this._ssvService.updateSSVState(request);
    }
    
    getGroupHeaderStyle(index: number): Object {
        if (this.columnGroups[index].highlighted)
            return {'width.px': this.columnGroups[index].width};
        else if (index == 0 && this.columnGroups.length == 1)
            return {'border-left': '1px solid #7493AF', 'width.px': this.columnGroups[index].width};
        else if (index == 0 && !this.columnGroups[index].highlighted && this.columnGroups[index+1].highlighted)
            return {'border-left': '1px solid #7493AF', 'border-right': 'none', 'width.px': this.columnGroups[index].width};
        else if (index == 0 && !this.columnGroups[index].highlighted && !this.columnGroups[index+1].highlighted)
            return {'border-left': '1px solid #7493AF', 'width.px': this.columnGroups[index].width};
        else if (!this.columnGroups[index].highlighted && (index + 1) < this.columnGroups.length && this.columnGroups[index+1].highlighted)
            return {'border-right': 'none', 'width.px': this.columnGroups[index].width};
        else 
            return {'width.px': this.columnGroups[index].width};
    }
    
    //Following functions support group expansion
    toggleGroupHighlight(groupPosition: number): void {
        for (let i = 0; i < this.columnGroups.length; i++) {
            if (i == groupPosition) 
                this.columnGroups[i].highlighted = !this.columnGroups[i].highlighted;
            else 
                this.columnGroups[i].highlighted = (this.columnGroups[i].highlighted ? false : this.columnGroups[i].highlighted); 
        }
    }
    
    //This will expand the group, given group position in the columnGroups vector, and collapse other groups
    expandGroup(groupPosition: number): void {
        for (let i = 0; i < this.columnGroups.length; i++) {
            this.columnGroups[i].expanded = (i == groupPosition ? true : false);
        }
        let currentGroup = this.columnGroups[groupPosition];
        this.expandedGroupChanged.emit(new ExpandedGroup(
            groupPosition,
            currentGroup.shortName,
            currentGroup.groupStartColumnPos,
            currentGroup.groupEndColumnPos
        ));
        // because this isn't the only component that can change group expansion,
        // the logic that updates the state of this template in response to the
        // change is centralized in ngOnChanges
    }
    
    undoExpansion() {
        for (let i = 0; i < this.columnGroups.length; i++) {
            this.columnGroups[i].expanded = false;  
            this.columnGroups[i].highlighted = false;
        }
        this.expandedGroupChanged.emit(null);
        // because this isn't the only component that can change group expansion,
        // the logic that updates the state of this template in response to the
        // change is centralized in ngOnChanges
    }
    //End of group expansion 
    
    selectSortColumnsBy(rows: SelectableRowData[]): void {
        if (rows && rows.length) {
            this.sortColumnsBy = rows[0];
            this.updateState();
        } else {
            this.sortColumnsBy = null;
        }
    }
    
    //For html can't access constant
    getHeatmapWidth(): number {
        return ColumnOptionsComponent.HEATMAP_WIDTH;
    }
}