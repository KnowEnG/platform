//visual example taken from https://bl.ocks.org/mbostock/3887051, customized to fit our design
import {Component, Input, OnChanges, SimpleChange} from '@angular/core';

@Component ({
    moduleId: module.id,
    selector: "grouped-barchart",
    templateUrl: './GroupedBarChart.html',
    styleUrls: ['./GroupedBarChart.css']
})

export class GroupedBarChart implements OnChanges {
    class = 'relative';

    @Input()
    data: Array<GroupedBarChartDataRecord>;
    
    @Input()
    configOption: GroupedBarChartConfigOption;
    
    @Input()
    maxXLabel: string = '';

    /** The scale for the x-coordinate of each bin. */
    binScale: any;

    /** The scale for the x-coordinate of each cohort bar. */
    barScale: any;

    /** The scale for the height of each cohort bar. */
    yScale: any;

    svgBorder: boolean = false;
    xLabel: string;
    binTitleLabel: string = '%Relative Abundance';
    svgMargin: any = {top: 4, right: 30, bottom: 4, left: 0};
    svgWidth: number = 220 - this.svgMargin.left - this.svgMargin.right;
    svgHeight: number = 34 - this.svgMargin.top - this.svgMargin.bottom;

    firstBinXPosition: number = 4 + this.svgMargin.left;
    dividerXPosition: number = 15 + this.svgMargin.left;
    mainAreaMarginLeft: number = 22 + this.svgMargin.left;

    cohorts: {[cohortName: string]: CohortInfo} = {
        'Baseline': new CohortInfo('baseline', 0),
        'Cohort 1': new CohortInfo('cohort1', 0),
        'Individual': new CohortInfo('individual', 0),
    };

    selectedBin: GroupedBarChartDataRecord = null;

    tooltipX: number = 0;
    tooltipY: number = 0;

    ngOnChanges(changes: {[propertyName: string]: SimpleChange}) {
        if (this.configOption) {
            if (this.configOption.width && this.configOption.svgMargin) {
                this.svgWidth = this.configOption.width - this.configOption.svgMargin.left - this.configOption.svgMargin.right;
                this.svgHeight = this.configOption.height - this.configOption.svgMargin.top - this.configOption.svgMargin.bottom;
                this.svgMargin = this.configOption.svgMargin;
                this.firstBinXPosition = 4 + this.svgMargin.left;
                this.dividerXPosition = 20 + this.svgMargin.left;
                this.mainAreaMarginLeft = 22 + this.svgMargin.left;
            }
            if (this.configOption.svgBorder)
                this.svgBorder = this.configOption.svgBorder;
            if (this.configOption.xLabel)
                this.xLabel = this.configOption.xLabel;
            if (this.configOption.binTitleLabel !== undefined)
                this.binTitleLabel = this.configOption.binTitleLabel;
        }
        var binNames: string[] = this.data.map((binData) => binData.binName);

        // get cohort sizes
        this.data.forEach((bin) => {
            bin.barDataRecords.forEach((bar) => {
               this.cohorts[bar.cohort].totalSize += bar.sampleSize;
            })
        });

        // split the full width by the number of bins
        // note: the first bin will appear in a separate area, so we use
        // the width of the separate area, and it shouldn't affect this scale,
        // so we use binNames.slice(1)
        this.binScale = d3.scale.ordinal()
            .rangeRoundBands([0, this.svgWidth-this.mainAreaMarginLeft], .1)
            .domain(binNames.slice(1));

        // split each bin in two, for the two primary cohorts
        this.barScale = d3.scale.ordinal()
            .rangeRoundBands([0, this.binScale.rangeBand()])
            .domain(['Baseline', 'Cohort 1']);

        // scale the maximum sampleSize to fill the height
        var maxY = d3.max(this.data, function(d: GroupedBarChartDataRecord) {
            return d3.max(d.barDataRecords, function(d: BarDataRecord) {
                if (d.sampleSize == 0) return 1; else return d.sampleSize;
            });
        });
        this.yScale = d3.scale.log() // or d3.scale.linear() for linear
            .range([0, this.svgHeight])
            .domain([1, maxY]);
    }
    /** Selects a bin, triggering the tooltip. */
    selectBin(bin: GroupedBarChartDataRecord, event: Event) {
        this.selectedBin = bin;
        this.tooltipX = (<any>event).clientX - 200;
        this.tooltipY = (<any>event).clientY - 100;
    }
    /** Deselects a bin. Won't change `selectedBin` if `selectedBin != bin`. */
    deselectBin(bin: GroupedBarChartDataRecord) {
        if (this.selectedBin === bin) {
            this.selectedBin = null;
        }
    }
    /** Returns the width of a bar. */
    barWidth(): number {
        return this.barScale.rangeBand();
    }
    /** Given a bin, returns its x-coordinate. */
    binOffset(bin: GroupedBarChartDataRecord): number {
        if (bin == this.data[0]) {
            return this.firstBinXPosition - this.mainAreaMarginLeft;
        }
        return this.binScale(bin.binName);
    }
    /** Given a bar, returns its x-coordinate. */
    barOffset(bar: BarDataRecord): number {
        return this.barScale(bar.cohort);
    }
    /** Given a bar, returns its height. */
    barHeight(bar: BarDataRecord): number {
        if (bar.sampleSize == 0) return 0; else return this.yScale(bar.sampleSize);
    }
    /** Given a bar, returns its css class. */
    barClass(bar: BarDataRecord): string {
        return this.cohorts[bar.cohort].className;
    }
    /** Given a bin, returns pretty (but less informative) label. */
    prettyBinLabel(bin: GroupedBarChartDataRecord) {
        return bin.binName.replace(/[\(\)\[\]]/g, '');
    }
}

class CohortInfo {
    constructor(
        public className: string, // css class
        public totalSize: number) { // total number of samples
    }
}

export class GroupedBarChartDataRecord {
    binName: string;
    barDataRecords: Array<BarDataRecord>;
}

export class BarDataRecord {
    cohort: string;
    sampleSize: number;
}

export class GroupedBarChartConfigOption {
    width: number;
    height: number;
    svgMargin: {
        top: number,
        right: number,
        bottom: number,
        left: number
    }
    svgBorder: boolean;
    xLabel: string;
    binTitleLabel: string;
}