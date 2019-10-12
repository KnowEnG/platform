import {Component, OnInit, OnChanges, SimpleChange, Input, TemplateRef, HostListener} from '@angular/core';

import {CellHeatmapEvent} from '../common/CellHeatmap';

@Component({
    moduleId: module.id,
    selector: 'heatmap-pane',
    templateUrl: './HeatmapPane.html',
    styleUrls: ['./HeatmapPane.css']
})

export class HeatmapPane implements OnInit, OnChanges {
    class = 'relative';

    @Input()
    heatmapData: number[][];

    @Input()
    title: string;

    @Input()
    rowLabels: any[] = [];

    @Input()
    initialShowLabels: boolean;

    @Input()
    tooltipContent: TemplateRef<any>;

    @Input()
    cellMetadataFetcher: (rowRank: number, colRank: number) => MainHeatmapCellMetadata;

    heatmapWidth = 750;

    showLabels: boolean;

    cellDetails: MainHeatmapCellMetadata = null;
    popoverTop: number = null;
    popoverLeft: number = null;
    offsetTop: number = 0;
    offsetLeft: number = 0;

    static categoricalPalette = ['#e15d63', '#00a8c9', '#fbba3d', '#063953', '#76ad98', '#ecd490', '#837ab5', '#abdee5', '#dc7f4f', '#567389', '#1D609E', '#E05869', '#7ED321', '#07ABAF', '#B5D1EB'];

    static missingValueColor = '#FFFFFF';

    constructor() { }

    ngOnInit() {
        this.showLabels = this.initialShowLabels;
    }

    ngOnChanges(changes: {[propertyName: string]: SimpleChange}) {
    }

    getCellHeight(): number {
        return this.showLabels ? 12 : 3;
    }

    /** Listens for and saves the scrolled page offsets when they change */
    @HostListener('window:scroll', ['$event'])
    doSomething(event: any) {
        this.offsetTop = window.pageYOffset;
        this.offsetLeft = window.pageXOffset;
    }

    /** When a cell is clicked, look up its metadata and display a popover near the clicked position */
    cellClicked(event: CellHeatmapEvent) {
        if (event.rowIndex != null && event.colIndex != null) {
            // popover has "position: abolute;", but clientX/Y are relative, so we
            // need to add the amount of page scroll to end up with the correct coordinates
            this.popoverTop =  this.offsetTop + event.event.clientY;
            this.popoverLeft = this.offsetLeft + event.event.clientX + 10;
            this.cellDetails = this.cellMetadataFetcher(event.rowIndex, event.colIndex);
        }
    }

    /** Clears fetched metadata and closes the CellDetails popover */
    closeCellDetails() {
        this.cellDetails = null;
        this.popoverLeft = null;
        this.popoverTop = null;
    }
}

export class MainHeatmapCellMetadata {
    constructor(
        public rowName: string,     // name of row containing this cell
        public sampleName: string,  // name of column containing this cell
        public value: number,       // numerical value of this cell
        public color: string) {     // color corresponding to cell's value
    }
}
