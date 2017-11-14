import {Component, Input, OnChanges, SimpleChange} from '@angular/core';

// note: this component requires d3.js

@Component ({
    moduleId: module.id,
    selector: 'difference-barchart',
    styleUrls: ['./DifferenceBarChart.css'],
    templateUrl: './DifferenceBarChart.html'
})

export class DifferenceBarChart implements OnChanges {
    class = 'relative';

    /** The value for the left side of the comparison. */
    @Input()
    leftValue: number;

    /** The value for the right side of the comparison. */
    @Input()
    rightValue: number;

    /** The maximum possible value for abs(`leftValue`-`rightValue`). */
    @Input()
    maxDifference: number;

    /**
     * The rectangle width in pixels for the case where
     * abs(`leftValue`-`rightValue`) = `maxDifference`.
     */
    @Input()
    maxRectangleWidth: number;

    /** The number of pixels to reserve for the text in the center. */
    @Input()
    centerWidth: number;

    /** The height of the svg. */
    @Input()
    height: number;

    /** The difference value. */
    difference: number = 0;

    /** The actual width of the current rectangle, based on `difference`. */
    rectangleWidth: number = 0;

    /** Updates the svg in response to changes. */
    ngOnChanges(changes: {[propertyName: string]: SimpleChange}): void {
        this.difference = this.leftValue - this.rightValue;
        this.rectangleWidth = d3.scale.linear()
            .domain([0, this.maxDifference])
            .range([0, this.maxRectangleWidth])(Math.abs(this.difference));
    }
}
