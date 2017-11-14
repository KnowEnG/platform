import {Component, OnChanges, Input, SimpleChange} from '@angular/core';

@Component ({
    moduleId: module.id,
    selector: 'abundance-barchart',
    templateUrl: './AbundanceBarChart.html',
    styleUrls: ['./AbundanceBarChart.css']
})

export class AbundanceBarChart implements OnChanges {
    class = 'relative';

    @Input()
    baselineAbundance: number;

    @Input()
    cohortAbundance: number;

    @Input()
    individualAbundance: number;

    @Input()
    width: number;

    @Input()
    height: number;

    data: Array<{width: number, style: string}>;

    barHeight: number;

    ngOnChanges(changes: {[propertyName: string]: SimpleChange}): void {
        var scale: any = d3.scale.linear()
            .domain([0, 100])
            .range([0, this.width]);

        this.data = [
            {width: scale(this.baselineAbundance), style: 'baseline'},
            {width: scale(this.cohortAbundance), style: 'cohort1'},
        ];
        if (this.individualAbundance !== undefined && this.individualAbundance !== null) {
            this.data.push({width: scale(this.individualAbundance), style: 'individual'});
        }
        this.barHeight = this.height / this.data.length;
    }
}
