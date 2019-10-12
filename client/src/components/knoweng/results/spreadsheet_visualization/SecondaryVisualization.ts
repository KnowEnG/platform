import {Component, Input, OnInit, OnChanges, SimpleChange} from '@angular/core';
import {NgClass} from '@angular/common';
import {DomSanitizer, SafeStyle} from '@angular/platform-browser';

import {Job} from '../../../../models/knoweng/Job';
import {SSVState, SSVStateRequest, Spreadsheet, Row, CategoricRow, RowStateRequest, MainSpreadsheetStateRequest} from '../../../../models/knoweng/results/SpreadsheetVisualization';
import {LogService} from '../../../../services/common/LogService';
import {SpreadsheetVisualizationService} from '../../../../services/knoweng/SpreadsheetVisualizationService';

import {SelectableRowData} from './SelectableTypes';
import {ColumnIndices} from './SSVOptions';

@Component({
    moduleId: module.id,
    selector: 'secondary-visualization',
    templateUrl: './SecondaryVisualization.html',
    styleUrls: ['./SecondaryVisualization.css']
})

export class SecondaryVisualization {
    class = 'relative';

    @Input()
    job: Job;

    @Input()
    state: SSVState;
    
    @Input()
    displayedColumns: ColumnIndices;
    
    //TODO: the new design has width of ~780px
    miniHeatmapWidth = 750;
    miniHeatmapHeight = 38;
    showRows: boolean = false;
    selectedFile: number = null;
    selectedRows: SelectableRowData[] = [];
    singleHeatmapDictionary: any = {};
    
    constructor(public logger: LogService, 
                public _sanitizer: DomSanitizer,
                public _ssVisualization: SpreadsheetVisualizationService) {
    }
    
    ngOnInit() {
    }
    
    ngOnChanges(changes: {[propertyName: string]: SimpleChange}): void {
        for (let propName in changes) {
            if (propName == 'state' && this.state && this.selectedRows.length > 0) {
                this.prepareMiniHeatmapData();
            } else if (propName == 'displayedColumns') {
                let previous = changes[propName].previousValue;
                let current = changes[propName].currentValue;
                if (!ColumnIndices.equal(previous, current)) {
                    this.setSingleHeatmapDictionary();
                }
            }
        }
    }
    
    toggleShowRows($event: MouseEvent): void {
        $event.preventDefault();
        $event.stopPropagation();
        this.showRows = !this.showRows;
    }
    
    showRowsChanged(value: boolean): void {
        this.showRows = false;
    }
    
    selectedRowsChanged(rows: SelectableRowData[]): void {
        this.selectedRows = rows;
        this.updateState();
    }
    getGradientCssForRow(row: SelectableRowData): SafeStyle {
        let domain = row.getColorScale().domain() as number[];
        let range = row.getColorScale().range();
        return this._sanitizer.bypassSecurityTrustStyle("linear-gradient(90deg, " +
            range.map((color: string, index: number) => color + " " + (100*domain[index]) + "%").join(", ") +
            ")");
    }
    onCheckboxChange(row: SelectableRowData): void {
        if (row.selected == false) {
            row.selected = true;
        } else {
            row.selected = false;
        }
    }
    
    updateState(): void {
        // Update the "otherRows" in our request and resubmit
        let orsr: RowStateRequest[] = [];
        if (this.selectedRows && this.selectedRows.length) {
            this.selectedRows.forEach((row: SelectableRowData) => {
                let request = new RowStateRequest(row.spreadsheet.spreadsheetId, row.rowIdx);
                orsr.push(request);
            });
        }
        
        let request = new SSVStateRequest(
            this.state.stateRequest.columnGroupingRowRequest,
            this.state.stateRequest.columnSortingRowRequest,
            this.state.stateRequest.mainSpreadsheetStateRequests,
            orsr,
            this.state.stateRequest.timeToEventEventRowRequest,
            this.state.stateRequest.timeToEventTimeRowRequest,
            this.state.stateRequest.timeToEventEventValue,
            this.state.stateRequest.timeToEventPvalRequests,
            null);
        this._ssVisualization.updateSSVState(request);
    }
    
    reverseSortByScore(): SelectableRowData[] {
        return this.selectedRows.sort(function(a, b) {
            let aScore = a.getScore();
            let bScore = b.getScore();
            if (aScore < bScore) {
                return 1;
            } else if (aScore > bScore) {
                return -1;
            } else {
                return 0;
            }
        });
    }
    
    prepareMiniHeatmapData(): void {
        this.selectedRows.forEach(row => row.updateData());
        //sort by row score
        this.selectedRows = this.selectedRows.sort(function(x, y) {return d3.ascending(x.getScore(), y.getScore());}); // sort ascending for now--these are currently pvals
        //initialize heapmap dictionary
        this.setSingleHeatmapDictionary()
    }
    
    setSingleHeatmapDictionary(): void {
        if (this.displayedColumns) {
            let index = 0;
            let singleheatmaps: any = {};
            this.selectedRows.forEach(row => {
                singleheatmaps[index] = row.getColorRGBValues().slice(this.displayedColumns.startPos, this.displayedColumns.endPos + 1);
                index++;
            });
            this.singleHeatmapDictionary = singleheatmaps;
        }
    }
}


