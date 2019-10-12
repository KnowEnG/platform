import {Component, AfterViewInit, OnChanges, SimpleChange, Input, ViewChild,
    ElementRef, Output, EventEmitter, ChangeDetectionStrategy} from '@angular/core';

@Component({
    moduleId: module.id,
    selector: 'cell-heatmap',
    templateUrl: './CellHeatmap.html',
    styleUrls: ['./CellHeatmap.css'],
    changeDetection: ChangeDetectionStrategy.OnPush
})


export class CellHeatmap implements AfterViewInit, OnChanges {
    class = 'relative';

    @Input()
    cellWidth: number;

    @Input()
    cellHeight: number;

    @Input()
    borderThickness: number;

    @Input()
    borderColor: string;

    @Input()
    selectedBorderThicknessMultiplier: number;

    @Input()
    selectedBorderColor: string;

    @Input()
    highlightColor: string;

    @Input()
    freezeHighlight: boolean;

    @Input()
    rowsOfColumns: string[][];
    
    @Input()
    DEBUG: boolean = false;

    @Output()
    cellMousedOver: EventEmitter<CellHeatmapEvent> = new EventEmitter<CellHeatmapEvent>();

    @Output()
    cellClicked: EventEmitter<CellHeatmapEvent> = new EventEmitter<CellHeatmapEvent>();

    numRows: number = null;
    numCols: number = null;

    changed: boolean = true;

    /** [rowIndex, colIndex] for last cell to receive a mouseover event. */
    mouseoverCell: number[] = [null, null];

    highlightData = {
        isOn: false,
        cellTop: null as number,
        cellLeft: null as number,
        rowBarHeight: null as number,
        colBarWidth: null as number
    };

    canvasContext: CanvasRenderingContext2D = null;

    /** reference to the template element that'll contain the canvas element. */
    @ViewChild('canvasElement') canvasElementRef: ElementRef;
    canvasNativeElement: HTMLCanvasElement = null;

    constructor() {
    }
    ngOnInit() {
    }
    ngOnDestroy() {
    }
    getCanvasWidth(): number {
        return this.numCols * (this.cellWidth + this.borderThickness) +
            2 * this.borderThickness;
    }
    getCanvasHeight(): number {
        return this.numRows * (this.cellHeight + this.borderThickness) +
            2 * this.borderThickness;
    }
    getRectangleX(colIndex: number, cellWidthInContext: number): number {
        return colIndex * (cellWidthInContext + this.borderThickness) +
            this.borderThickness;
    }
    getRectangleY(rowIndex: number, cellHeightInContext: number): number {
        return rowIndex * (cellHeightInContext + this.borderThickness) +
            this.borderThickness;
    }
    /**
     * Handles changes to the inputs after ngAfterViewInit, whenever the parent component changes our
     * inputs.
     */
    ngOnChanges(changes: {[propertyName: string]: SimpleChange}) {
        if (this.canvasNativeElement) {
            if (this.DEBUG) {
                console.log("property changed... redrawing!", changes);
                console.time('redraw');
            }

            // Redraw when heatmap contents change
            this.drawCells();

            if (this.DEBUG) {
                console.timeEnd('redraw');
            }
        }
    }
    ngAfterViewInit() {
        // get the context
        this.drawCells();
    }
    drawCells(): void {
        if (this.DEBUG) {
            console.log('Drawing all cells...')
            console.time('draw_cells');
        }
        // initialize size vars
        this.numRows = this.rowsOfColumns.length;
        this.numCols = (this.numRows > 0 ? this.rowsOfColumns[0].length : 0);

        this.canvasNativeElement = this.canvasElementRef.nativeElement;
        this.canvasContext = this.canvasNativeElement.getContext('2d', {alpha: false});

        // what happens if cellWidth or cellHeight is less than 1px?
        // we'll create a larger canvas such that each cell is at least 1px x 1px,
        // and then we'll adjust the css width and height of the canvas element,
        // which will usually result in the GPU doing the work. that beats
        // trying to write an efficient implementation of the same in js, and it
        // also prevents anti-aliasing from washing out the colors.

        // in fact, we can do the same thing whenever cellWidth or cellHeight is
        // not an integer, as long as borderThickness is 0 (for the current
        // implementation, anyway). that'll prevent the anti-aliasing artifacts we
        // see when, e.g., cellWidth = 1.9.

        // set the canvas width and height depending on whether we have subpixel
        // cellWidth or cellHeight
        let workingCellWidth = null as number;
        let canvasWidth = null as number;
        if (this.borderThickness == 0 && !Number.isInteger(this.cellWidth)) {
            workingCellWidth = 1;
            canvasWidth = workingCellWidth * this.numCols;
        } else {
            workingCellWidth = this.cellWidth;
            canvasWidth = this.getCanvasWidth();
        }
        this.canvasContext.canvas.width = canvasWidth;

        let workingCellHeight = null as number;
        let canvasHeight = null as number;
        if (this.borderThickness == 0 && !Number.isInteger(this.cellHeight)) {
            workingCellHeight = 1;
            canvasHeight = workingCellHeight * this.numRows;
        } else {
            workingCellHeight = this.cellHeight;
            canvasHeight = this.getCanvasHeight();
        }
        this.canvasContext.canvas.height = canvasHeight;

        // always set the css width and height to match the desired size of the
        // rendered heatmap
        this.canvasNativeElement.style.setProperty('width', this.getCanvasWidth() + 'px');
        this.canvasNativeElement.style.setProperty('height', this.getCanvasHeight() + 'px');

        // paint background
        this.canvasContext.fillStyle = this.borderColor;
        this.canvasContext.fillRect(0, 0, canvasWidth, canvasHeight);

        this.rowsOfColumns.forEach((row: string[], rowIndex: number) => {
            row.forEach((cellColor: string, colIndex: number) => {
                this.drawCell(rowIndex, colIndex, cellColor, workingCellWidth, workingCellHeight);
            });
        });

        if (this.DEBUG) {
            console.timeEnd('draw_cells');
        }
    }
    drawCell(rowIndex: number, colIndex: number, cellColor: string,
            workingCellWidth: number, workingCellHeight: number): void {
        // draw rectangle
        this.canvasContext.fillStyle = cellColor;
        this.canvasContext.fillRect(
            this.getRectangleX(colIndex, workingCellWidth),
            this.getRectangleY(rowIndex, workingCellHeight),
            workingCellWidth,
            workingCellHeight);
    }
    onMouseout(event: MouseEvent): void {
        // mouse has left the canvas
        if (!this.freezeHighlight) {
            this.mouseoverCell = [null, null];
            this.highlightCell(this.mouseoverCell[0], this.mouseoverCell[1]);
            this.cellMousedOver.emit(new CellHeatmapEvent(null, null, event));
        }
    }
    onMousemove(event: MouseEvent): void {
        if (!this.freezeHighlight) {
            let rowAndColIndex = this.getRowAndColIndexForMouseEvent(event);
            if (rowAndColIndex.rowIndex != this.mouseoverCell[0] ||
                    rowAndColIndex.colIndex != this.mouseoverCell[1]) {
                this.mouseoverCell = [rowAndColIndex.rowIndex, rowAndColIndex.colIndex];
                this.highlightCell(this.mouseoverCell[0], this.mouseoverCell[1]);
                this.cellMousedOver.emit(new CellHeatmapEvent(
                    rowAndColIndex.rowIndex, rowAndColIndex.colIndex, event));
            }
        }
    }
    onClick(event: MouseEvent): void {
        let rowAndColIndex = this.getRowAndColIndexForMouseEvent(event);
        this.cellClicked.emit(new CellHeatmapEvent(
            rowAndColIndex.rowIndex, rowAndColIndex.colIndex, event));
    }
    getRowAndColIndexForMouseEvent(event: MouseEvent): {rowIndex: number, colIndex: number} {
        let canvasRect = this.canvasNativeElement.getBoundingClientRect();
        let x = event.clientX - canvasRect.left;
        let y = event.clientY - canvasRect.top;
        // for the purposes of this method, we'll consider the left border of
        // the cell as part of the column. we'll also consider the right border
        // of the rightmost cell as part of that column.
        let colIndex = Math.min(
            Math.floor(x / (this.cellWidth + this.borderThickness)), this.numCols - 1);
        // for the purposes of this method, we'll consider the top border of
        // the cell as part of the row. we'll also consider the bottom border
        // of the bottommost cell as part of that row.
        let rowIndex = Math.min(
            Math.floor(y / (this.cellHeight + this.borderThickness)), this.numRows - 1);
        let returnVal = {rowIndex, colIndex};
        return returnVal;
    }
    highlightCell(rowIndex: number, colIndex: number): void {
        if (rowIndex !== null && colIndex !== null) {
            this.highlightData.isOn = true;
            this.highlightData.cellTop = this.getRectangleY(rowIndex, this.cellHeight);
            this.highlightData.cellLeft = this.getRectangleX(colIndex, this.cellWidth);
            // ensure the highlight bars are wide/tall enough to be rendered
            this.highlightData.rowBarHeight = Math.max(1, this.cellHeight);
            this.highlightData.colBarWidth = Math.max(1, this.cellWidth);
        } else {
            this.highlightData.isOn = false;
        }
    }
}

export class CellHeatmapEvent {
    constructor(
        public rowIndex: number,
        public colIndex: number,
        public event: MouseEvent) {
    }
}
