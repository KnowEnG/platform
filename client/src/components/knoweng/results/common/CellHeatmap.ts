/// <reference path="../../../../typings/pixi.js/pixi.js.d.ts" />
import {Component, AfterViewInit, OnChanges, SimpleChange, Input, ViewChild, ElementRef, Output, EventEmitter, NgZone} from '@angular/core';

@Component({
    selector: 'cell-heatmap',
    template: `<div #canvasHost></div>`,
    styleUrls: []
})

export class CellHeatmap implements AfterViewInit, OnChanges {

    @Input()
    cellWidth: number;

    @Input()
    cellHeight: number;

    @Input()
    borderThickness: number;

    @Input()
    selectedBorderThicknessMultiplier: number;

    @Input()
    selectedBorderColor: number;

    @Input()
    highlightColor: number;

    @Input()
    updateHighlight: boolean;

    @Input()
    rowsOfColumns: number[][];

    @Output()
    cellMousedOver: EventEmitter<CellHeatmapEvent> = new EventEmitter<CellHeatmapEvent>();

    @Output()
    cellClicked: EventEmitter<CellHeatmapEvent> = new EventEmitter<CellHeatmapEvent>();

    renderer: PIXI.WebGLRenderer | PIXI.CanvasRenderer = null;
    stage: PIXI.Container = null;

    loading: boolean;
    
    overlay: PIXI.Container = null;

    numRows: number = null;
    numCols: number = null;

    changed: boolean = true;

    /** [rowIndex, colIndex] for last cell to receive a mouseover event. */
    mouseoverCell: number[] = [null, null];

    /** reference to the template element that'll contain the canvas element. */
    @ViewChild('canvasHost') canvasHost: ElementRef;

    constructor(public ngZone: NgZone) {
    }
    ngOnInit() {
        // create the renderer
        this.renderer = new PIXI.CanvasRenderer(
            0, 0, // we'll resize in ngOnChanges
            {antialias: false, transparent: true, resolution: 1}
        );
        this.renderer.autoResize = false;

        this.drawCells();
    }
    ngOnDestroy() {
        if (this.overlay) {
            this.overlay.destroy(true);
            this.overlay = undefined;
        }
        
        if (this.stage) {
            this.stage.destroy(true);
            this.stage = undefined;
        }
        
        if (this.renderer) {
            this.renderer.destroy(true);
            this.renderer = undefined;
        }
    }
    getCanvasWidth(): number {
        return this.numCols * (this.cellWidth + this.borderThickness) +
            2 * this.borderThickness;
    }
    getCanvasHeight(): number {
        return this.numRows * (this.cellHeight + this.borderThickness) +
            2 * this.borderThickness;
    }
    getRectangleX(colIndex: number): number {
        return colIndex * (this.cellWidth + this.borderThickness) +
            this.borderThickness;
    }
    getRectangleY(rowIndex: number): number {
        return rowIndex * (this.cellHeight + this.borderThickness) +
            this.borderThickness;
    }
    /**
     * Handles changes to the inputs after ngAfterViewInit, whenever the parent component changes our
     * inputs.
     */
    ngOnChanges(changes: {[propertyName: string]: SimpleChange}) {
        if (!this.renderer) {
            return;
        }

        this.drawCells();
    }
    ngAfterViewInit() {
        // add the canvas to the DOM
        let nativeElement: any = this.canvasHost.nativeElement;
        nativeElement.appendChild(this.renderer.view);

        // start update loop
        this.update();
    }
    drawCells(): void {
        // initialize size vars
        this.numRows = this.rowsOfColumns.length;
        this.numCols = (this.numRows > 0 ? this.rowsOfColumns[0].length : 0);
        
        let newWidth: number = this.getCanvasWidth();
        let newHeight: number = this.getCanvasHeight();
        
        // do we need to resize the canvas?
        if (newWidth != this.renderer.width || newHeight != this.renderer.height) {
            this.renderer.resize(newWidth, newHeight);
        }
        
        let newStage: PIXI.Container = new PIXI.Container();
        // detect mouse leaving canvas
        newStage.interactive = true;
        newStage.hitArea = new PIXI.Rectangle(0, 0, this.getCanvasWidth(), this.getCanvasHeight());
        (<any>newStage).mouseout = (event: PIXI.interaction.InteractionEvent) => this.onMouseout(event);

        this.rowsOfColumns.forEach((row: number[], rowIndex: number) => {
            row.forEach((cellColor: number, colIndex: number) => {
                this.drawCell(newStage, rowIndex, colIndex, cellColor);
            });
        });

        let oldStage: PIXI.Container = this.stage;
        this.stage = newStage;

        // destroy the old stage
        if (oldStage !== null) {
            oldStage.destroy(true);
            oldStage = undefined;
        }

        this.changed = true;
    }
    drawCell(
            stage: PIXI.Container,
            rowIndex: number,
            colIndex: number,
            cellColor: number): void {
        // draw rectangle
        var rectangle: PIXI.Graphics = new PIXI.Graphics();
        rectangle.beginFill(cellColor);
        rectangle.drawRect(0, 0, this.cellWidth, this.cellHeight);
        rectangle.endFill();
        // add interactivity
        rectangle.interactive = true;
        rectangle.hitArea = new PIXI.Rectangle(0, 0, this.cellWidth, this.cellHeight);
        (<any>rectangle).mouseover = (event: PIXI.interaction.InteractionEvent) => this.onMouseover(event, rowIndex, colIndex);
        (<any>rectangle).click = (event: PIXI.interaction.InteractionEvent) => this.onClick(event, rowIndex, colIndex);
        // position
        rectangle.x = this.getRectangleX(colIndex);
        rectangle.y = this.getRectangleY(rowIndex);
        // add to stage
        stage.addChild(rectangle);
    }
    onMouseout(event: PIXI.interaction.InteractionEvent): void {
        // mouse has left the canvas
        if (this.updateHighlight) {
            this.mouseoverCell = [null, null];
        }
        // note: could reduce calls to highlightCell by checking for changes
        // in mouseoverCell; seems to need a little help after a click event
        this.highlightCell(this.mouseoverCell[0], this.mouseoverCell[1]);
        this.cellMousedOver.emit(new CellHeatmapEvent(
            null, null, <MouseEvent>event.data.originalEvent));
    }
    onMouseover(event: PIXI.interaction.InteractionEvent, rowIndex: number, colIndex: number): void {
        if (this.updateHighlight) {
            this.mouseoverCell = [rowIndex, colIndex];
        }
        // note: could reduce calls to highlightCell by checking for changes
        // in mouseoverCell; seems to need a little help after a click event
        this.highlightCell(this.mouseoverCell[0], this.mouseoverCell[1]);
        this.cellMousedOver.emit(new CellHeatmapEvent(
            rowIndex, colIndex, <MouseEvent>event.data.originalEvent));
    }
    onClick(event: PIXI.interaction.InteractionEvent, rowIndex: number, colIndex: number): void {
        this.cellClicked.emit(new CellHeatmapEvent(
            rowIndex, colIndex, <MouseEvent>event.data.originalEvent));
    }
    // note: could use mouseoverCell directly; let's see how that shakes out
    highlightCell(rowIndex: number, colIndex: number): void {
        if (this.overlay !== null) {
            this.stage.removeChild(this.overlay);
            this.overlay.destroy(true);
        }
        this.overlay = new PIXI.Container();

        if (rowIndex !== null && colIndex !== null) {
            // draw a border around the selected cell
            var rectangle: PIXI.Graphics = new PIXI.Graphics();
            rectangle.lineStyle(this.selectedBorderThicknessMultiplier * this.borderThickness, this.selectedBorderColor, 1);
            rectangle.drawRect(0, 0, this.cellWidth, this.cellHeight);
            rectangle.x = this.getRectangleX(colIndex);
            rectangle.y = this.getRectangleY(rowIndex);
            this.overlay.addChild(rectangle);

            // highlight the path from the current cell back to its column label
            if (rowIndex > 0) {
                var colHighlight: PIXI.Graphics = new PIXI.Graphics();
                colHighlight.beginFill(this.highlightColor, 0.5);
                colHighlight.drawRect(0, 0, this.cellWidth, rowIndex * (this.cellHeight + this.borderThickness));
                colHighlight.endFill();
                colHighlight.x = this.getRectangleX(colIndex);
                colHighlight.y = 0;
                this.overlay.addChild(colHighlight);
            }

            // highlight the path from the current cell back to its row label
            if (colIndex > 0) {
                var rowHighlight: PIXI.Graphics = new PIXI.Graphics();
                rowHighlight.beginFill(this.highlightColor, 0.5);
                rowHighlight.drawRect(0, 0, colIndex * (this.cellWidth + this.borderThickness), this.cellHeight);
                rowHighlight.endFill();
                rowHighlight.x = 0
                rowHighlight.y = this.getRectangleY(rowIndex);
                this.overlay.addChild(rowHighlight);
            }
        }

        this.stage.addChild(this.overlay);
        this.changed = true;
    }
    update(): void {
        if (!this.renderer || !this.stage) {
            return;
        }
        
        this.ngZone.runOutsideAngular(() => {
            requestAnimationFrame(() => this.update());
        });
        
        if (this.changed) {
            this.renderer.render(this.stage);
            this.changed = false;
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

/* hex input should begin with 0x */
export function hexToDec(hex: string): number {
    return parseInt(hex.replace(/^#/, ''), 16);
}
