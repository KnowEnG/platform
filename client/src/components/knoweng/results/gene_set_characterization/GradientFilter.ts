import {Component, Input, OnInit, OnChanges, SimpleChange, Output, EventEmitter} from '@angular/core';

@Component ({
    moduleId: module.id,
    selector: 'gradient-filter',
    styleUrls: ['./GradientFilter.css'],
    templateUrl: './GradientFilter.html'
})

export class GradientFilter implements OnInit, OnChanges {
    class = 'relative';

    @Input()
    leftValue: number;

    @Input()
    rightValue: number;

    @Input()
    initialValue: number;

    @Input()
    leftColor: string;

    @Input()
    rightColor: string;

    @Output()
    currentValue: EventEmitter<number> = new EventEmitter<number>();

    xScale: any = null;

    /** width of gradient area in pixels */
    width: number = 276;

    /** height of gradient area in pixels */
    height: number = 49;

    /** border thickness in pixels */
    borderThickness: number = 4;

    currentX: number;

    constructor() {
    }

    ngOnInit() {
        // poor browser support for drag events on svg elements, so using d3
        // TODO monitor ng2 releases for alternative API

        // define drag behaviors
        var drag: any = d3.behavior.drag()
            .on("drag", () => this.onDrag())
            .on("dragend", () => this.onDragEnd());

        // respond to drag events on the thresholdGroup
        d3.select('.gradient-filter-container .slider').call(drag);
    }

    /** Handles updates to the inputs. */
    ngOnChanges(changes: {[propertyName: string]: SimpleChange}) {
        let update: boolean = false;
        for (let propName in changes) {
            if (propName != 'initialValue') {
                update = true;
                break;
            }
        }
        if (update) {
            this.xScale = d3.scale.linear()
                .domain([this.leftValue, this.rightValue])
                .range([0, this.width]);
            this.currentX = this.xScale(this.initialValue);
            this.currentValue.emit(this.xScale.invert(this.currentX));
        }
    }

    /**
     * Handles a change in the drag position while the drag is still in
     * progress.
     */
    onDrag(): void {
        // get new position and change in position
        // note: use .x instead of .clientX on d3.event
        var newX: number = (<DragEvent>d3.event).x;

        // constrain position to plot
        var range = this.xScale.range();
        if (newX < range[0]) {
            newX = range[0];
        } else if (newX > range[1]) {
            newX = range[1];
        }
        this.currentX = newX;
    }
    /**
     * Handles the completion of a drag.
     */
    onDragEnd(): void {
        this.currentValue.emit(this.xScale.invert(this.currentX));
    }
}
