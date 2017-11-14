import {Component, Input, OnInit, OnChanges, SimpleChange, Output, EventEmitter} from '@angular/core';

@Component ({
    moduleId: module.id,
    selector: 'slider',
    styleUrls: ['./Slider.css'],
    templateUrl: './Slider.html'
})

export class Slider implements OnInit, OnChanges {
    class = 'relative';

    @Input()
    leftValue: number;

    @Input()
    rightValue: number;

    @Input()
    initialValue: number;

    @Output()
    updatedCurrentValue: EventEmitter<number> = new EventEmitter<number>();

    xScale: any = null;

    /** width of slider in pixels */
    width: number = 243;

    /** height of sider in pixels */
    height: number = 7;

    controlRadius: number = 8.5;

    currentX: number;
    currentValue: number;

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
        d3.select('.slider-container .control').call(drag);
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
            this.updateCurrentValue();
        }
    }
    updateCurrentValue(): void {
        this.currentValue = d3.round(this.xScale.invert(this.currentX));
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
        this.updateCurrentValue();
        this.updatedCurrentValue.emit(this.currentValue);
    }
}
