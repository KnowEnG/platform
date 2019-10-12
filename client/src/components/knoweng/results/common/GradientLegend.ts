import {Component, Input, OnChanges, SimpleChange} from '@angular/core';

@Component ({
    moduleId: module.id,
    selector: 'gradient-legend',
    styleUrls: ['./GradientLegend.css'],
    templateUrl: './GradientLegend.html'
})

export class GradientLegend implements OnChanges {
    class = 'relative';

    @Input()
    leftValue: number;

    @Input()
    rightValue: number;

    @Input()
    leftColor: string;

    @Input()
    rightColor: string;

    /** width of bar in pixels */
    width: number = 282;

    /** height of bar in pixels */
    height: number = 15;

    constructor() {
    }

    /** Handles updates to the inputs. */
    ngOnChanges(changes: {[propertyName: string]: SimpleChange}) {
    }
}
