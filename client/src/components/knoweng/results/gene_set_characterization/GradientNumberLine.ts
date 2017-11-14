import {Component, Input, OnChanges, SimpleChange} from '@angular/core';

@Component ({
    moduleId: module.id,
    selector: 'gradient-number-line',
    styleUrls: ['./GradientNumberLine.css'],
    templateUrl: './GradientNumberLine.html'
})

export class GradientNumberLine implements OnChanges {
    class = 'relative';

    @Input()
    leftValue: number;

    @Input()
    rightValue: number;

    @Input()
    currentValue: number;

    @Input()
    leftColor: string;

    @Input()
    rightColor: string;

    xScale: any = null;

    /** width of number line in pixels */
    lineWidth: number = 385;

    /** height of number line in pixels */
    lineHeight: number = 9;

    /** paddingLeft and paddingRight need to fit the currentValue label when
     *  it appears at either extreme of the range.
     */
    paddingLeft: number = 20;
    paddingRight: number = 20;
    tickSpillTop: number = 3;
    tickSpillBottom: number = 13;

    currentX: number;

    constructor() {
    }

    /** Handles updates to the inputs. */
    ngOnChanges(changes: {[propertyName: string]: SimpleChange}) {
        this.xScale = d3.scale.linear()
            .domain([this.leftValue, this.rightValue])
            .range([0, this.lineWidth]);
        this.currentX = this.xScale(this.currentValue);
    }
}
