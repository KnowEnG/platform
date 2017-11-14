import {Component, Input} from '@angular/core';

@Component ({
    moduleId: module.id,
    selector: 'pie-chart',
    styleUrls: ['./PieChart.css'],
    templateUrl: './PieChart.html'
})

export class PieChart {
    class = 'relative';

    @Input()
    radius: number;

    @Input()
    percentage: number;

    @Input()
    sliceColor: string;

    @Input()
    remainderColor: string;

    constructor() {
    }
}
