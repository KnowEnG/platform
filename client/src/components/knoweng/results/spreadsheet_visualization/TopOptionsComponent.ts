import {Component, OnInit, OnChanges, SimpleChange, Input, Output, EventEmitter} from '@angular/core';

import {SSVState, Spreadsheet} from '../../../../models/knoweng/results/SpreadsheetVisualization';
import {SelectablePrimarySpreadsheet} from './SelectableTypes';
import {ColumnIndices, ExpandedGroup} from './SSVOptions';

@Component({
    moduleId: module.id,
    selector: 'top-options',
    templateUrl: './TopOptionsComponent.html',
    styleUrls: ['./TopOptionsComponent.css']
})

export class TopOptionsComponent implements OnInit, OnChanges {
    
    //This is number pixels of the page turning widge width. The number is based on design.
    static readonly TOTAL_PAGE_TURNER_WIDTH: number = 130;
    static readonly MIN_CELL_WIDTH: number = 3;
    static readonly MIN_HEATMAP_WIDTH: number = 750;
    
    @Input()
    state: SSVState;

    @Input()
    selectablePrimarySpreadsheets: SelectablePrimarySpreadsheet[];  

    @Input()
    expandedGroup: ExpandedGroup;

    @Input()
    displayedColumns: ColumnIndices;

    @Output()
    spreadsheetToggled = new EventEmitter<SelectablePrimarySpreadsheet>();
    
    @Output()
    displayedColumnsChanged = new EventEmitter<ColumnIndices>();
    
    @Output()
    closingGroup = new EventEmitter<ExpandedGroup>();
    
    showSpreadsheetsPanel: boolean = false;
    totalColumnCount: number = 0;
    currentPagePos: number = 1;
    showBirdseyeView: boolean = true;
    
    ngOnInit() {
    }
    
    ngOnChanges(changes: {[propertyName: string]: SimpleChange}) {
        for (let propName in changes) {
            if (propName == 'state' && this.state) {
                this.totalColumnCount = this.state.orderedSampleNames.length;
            } else if (propName == 'displayedColumns') {
                this.showBirdseyeView = this.displayedColumns.isShowingAll();
            }
        }
    }
    
    /**
     * Close or open the dropdown menu (spreadsheets panel) 
     **/
    toggleSpreadsheetsPanel($event: MouseEvent) {
        $event.preventDefault();
        $event.stopPropagation();
        this.showSpreadsheetsPanel = !this.showSpreadsheetsPanel;
    }
    
    /**
     * Select a spreadsheet so its heatmap will be shown in the main heapmap area; Deselect a spreadsheet so its heatmap will be hidden
     **/
    toggleSpreadsheet(sps: SelectablePrimarySpreadsheet): void {
        this.spreadsheetToggled.emit(sps);
    }
    
    /**
     * Compute the pixel width of the page rectangle 
     **/
    getPageWidthOnTurner(): number {
        let totalpages = this.getTotalPages();
        if (totalpages < 1) {
            return TopOptionsComponent.TOTAL_PAGE_TURNER_WIDTH;
        }
        let pagewidth = TopOptionsComponent.TOTAL_PAGE_TURNER_WIDTH / totalpages;
        //If we have total of non-integer count of pages, 7.45 pages for example, 
        //and currentPagePos is advanced to 8, we would only display width for .45 page
        if (this.currentPagePos > totalpages) {
            pagewidth = pagewidth * (totalpages + 1 - this.currentPagePos);
        }        
        return pagewidth;
    }

    getTotalPageTurnerWidth(): number {
        return TopOptionsComponent.TOTAL_PAGE_TURNER_WIDTH;
    }
    
    /**
     * Compute the pixel width of the rectangle area to the left of page rectangle
     */
    getPageTurnerLeftWidth(): number {
        let totalpages = this.getTotalPages();
        let leftwidth = 0;
        let pagewidth = TopOptionsComponent.TOTAL_PAGE_TURNER_WIDTH / totalpages;
        if (this.currentPagePos > 1 )
            leftwidth = pagewidth * (this.currentPagePos - 1);
        return leftwidth;
     }
     
    /**
     * Compute the pixel width of the rectangle area to the right of page rectangle
     **/ 
    getPageTurnerRightWidth(): number {
        let totalpages = this.getTotalPages();
        let rightwidth = 0;
        if (this.currentPagePos <= totalpages) {
            let pagewidth = TopOptionsComponent.TOTAL_PAGE_TURNER_WIDTH / totalpages;
            rightwidth = pagewidth * (totalpages - this.currentPagePos);
        } 
        return rightwidth;
    }
    
    pageLeft() {
        this.currentPagePos = (this.currentPagePos > 1) ? this.currentPagePos - 1 : this.currentPagePos;
        this.updateDisplayedColumnIndices();
    }
    
    pageRight() {
        let totalpages = this.getTotalPages();
        this.currentPagePos = (this.currentPagePos < totalpages) ? this.currentPagePos + 1 : this.currentPagePos;
        this.updateDisplayedColumnIndices();
    }
    
    /**
     * update firstDisplayedColumnIndex and lastDisplayedColumnIndex, those two indices are only relevant to pagination and birdseye view. 
     * This will also allow user to go back to where view state was before group expansion
     */
    updateDisplayedColumnIndices() {
        let totalpages = this.getTotalPages();
        let firstDisplayedColumnIndex: number = 0;
        let lastDisplayedColumnIndex: number = 0;
        if (totalpages <= 1) {
            lastDisplayedColumnIndex = this.totalColumnCount - 1;
        } else {
            firstDisplayedColumnIndex = (this.currentPagePos - 1) * this.getNumColumnsPerPage();
            if (this.currentPagePos < totalpages) 
                lastDisplayedColumnIndex = this.currentPagePos * this.getNumColumnsPerPage() - 1;
            else
                lastDisplayedColumnIndex = this.totalColumnCount - 1;
        }
        let newIndices = new ColumnIndices(
            firstDisplayedColumnIndex, lastDisplayedColumnIndex, this.totalColumnCount);
        this.displayedColumnsChanged.emit(newIndices);
    }
    
    toggleBirdsEyeView() {
        this.showBirdseyeView = !this.showBirdseyeView;
        if (this.showBirdseyeView) {
            let newIndices: ColumnIndices = new ColumnIndices(0, this.totalColumnCount - 1, this.totalColumnCount);
            this.displayedColumnsChanged.emit(newIndices);
        } else {
            this.updateDisplayedColumnIndices();
        }
    }
    
    /**NOTE to Matt: here I tried to output some signal when "UNDO EXPANSION" is clicked from top component,
     * so the group by column single row heatmap can returned to unexpanded state. But I did not get this to work.
     * The undo expansion on the single row heatmap header works though.
     **/
    undoExpansion() {
        this.expandedGroup = null;
        this.closingGroup.emit(this.expandedGroup);
        this.updateDisplayedColumnIndices();
    }

    private getTotalPages(): number {
        //the total pages could be decimal like 1.35 pages
        return this.totalColumnCount / this.getNumColumnsPerPage();
    }

    private getNumColumnsPerPage(): number {
        return Math.floor(TopOptionsComponent.MIN_HEATMAP_WIDTH / TopOptionsComponent.MIN_CELL_WIDTH);
    }
}