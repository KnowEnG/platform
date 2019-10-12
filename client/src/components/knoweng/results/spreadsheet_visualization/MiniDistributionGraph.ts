import {Component, OnChanges, SimpleChange, Input} from '@angular/core';
import {SelectableRowData} from './SelectableTypes';
import {NumberFormatPipe} from '../../../../pipes/knoweng/NumberFormatPipe';

@Component({
    moduleId: module.id,
    selector: 'mini-distribution-graph',
    templateUrl: './MiniDistributionGraph.html',
    styleUrls: ['./MiniDistributionGraph.css'],
})

export class MiniDistributionGraph implements OnChanges {
    class = 'relative';

    @Input()
    rowDisplayData: SelectableRowData;

    plotAreaWidth = 86; // make it a multiple of binWidthForNumeric
    plotAreaHeight = 34; // the height reserved for plotting frequency data

    colorBarHeight = 4; // the height reserved for plotting the color bar/legend
    xLegendHeight = 8; // the height reserved for plotting the x-axis legend for numeric rows

    topMargin = 3;
    rightMargin = 25;
    bottomMargin = 3;
    leftMargin = 2;

    rowType: string = null; // for convenience
    totalCount: number = null; // for convenience

    xMin = 0;
    xMax = 0;
    yMin = 0;
    yMax = 0;

    binWidthForNumeric = 2;

    yScale: any; // d3 doesn't export Linear<number, number>
    path: string = null;

    patternId: string;
    gradientStops: GradientStop[] = null; // iff numeric
    patternSegments: PatternSegment[] = null; // iff categorical
    bins: Bin[] = null;

    currentBin: Bin = null;
    popoverTop = 0;
    popoverLeft = 0;

    constructor() {
        // need a unique id for the svg defs
        this.patternId = "pattern" + Math.random().toString().substring(2);
    }
    ngOnChanges(changes: {[propertyName: string]: SimpleChange}) {
        if (this.rowDisplayData.getRawRow() && this.rowDisplayData.getColorScale() && this.rowDisplayData.getColorRGBValues().length > 0) {
            this.calculateLayout();
        }
    }
    calculateLayout(): void {
        this.rowType = this.rowDisplayData.getType();
        if (this.rowType == 'numeric') {
            let values = this.rowDisplayData.getRawRow().getValuesOrderedBySampleNames() as number[];
            this.totalCount = values.length;
            let colorScale = this.rowDisplayData.getColorScale() as d3.scale.Linear<string, string>;
            let range = colorScale.range();
            let colorScaleDomain = colorScale.domain(); // normalized
            let rawDomain = this.rowDisplayData.getValueRange() as number[];
            this.xMin = rawDomain[0];
            this.xMax = rawDomain[1];
            // FIXME flip direction on these?
            this.gradientStops = range.map((color: string, index: number) => {
                return new GradientStop(color, 100*colorScaleDomain[index] + "%");
            });
            this.patternSegments = null;
            let numMissingValues = values.filter((val) => val === null).length;
            let numBins = this.plotAreaWidth / this.binWidthForNumeric;
            let histoData = d3.layout.histogram()
                .bins(numMissingValues > 0 ? numBins-1 : numBins)(values.filter((val) => val !== null));
            let formatter = new NumberFormatPipe();
            this.bins = histoData.map((datum, index) => {
                let label = formatter.transform(datum.x) + '-' + formatter.transform(datum.x + datum.dx);
                return new Bin(
                    label,
                    this.plotAreaWidth * index/numBins,
                    this.plotAreaWidth * (index+1)/numBins,
                    datum.y,
                    null,
                    false);
            });
            if (numMissingValues > 0) {
                this.bins.push(new Bin(
                    null,
                    this.plotAreaWidth * (numBins-1)/numBins,
                    this.plotAreaWidth,
                    numMissingValues,
                    null,
                    true
                ));
            }
            // prepare to scale counts to heights
            this.yMax = d3.max(this.bins, (bin) => bin.count);
            this.yScale = d3.scale.linear()
                .domain([0, this.yMax])
                .range([this.plotAreaHeight - this.xLegendHeight, 2]); // leave a little room at the top
            // create one data point per bin + a leftmost data point + a rightmost data point
            let points: [number, number][] = [];
            this.bins.forEach((bin, index) => {
                if (index == 0) {
                    // use left edge of bin for leftmost point
                    points.push([bin.xMin, this.yScale(bin.count)]);
                }
                // use center of bin
                points.push([(bin.xMax + bin.xMin)/2, this.yScale(bin.count)]);
                if (index == this.bins.length - 1) {
                    // use right edge of bin for rightmost point
                    points.push([bin.xMax, this.yScale(bin.count)]);
                }
            });
            this.path = d3.svg.line().interpolate("monotone")(points);
        } else if (this.rowType == 'categoric') {
            let values = this.rowDisplayData.getRawRow().getValuesOrderedBySampleNames() as string[];
            this.totalCount = values.length;
            let colorScale = this.rowDisplayData.getColorScale() as d3.scale.Ordinal<string, {}>;
            let range = colorScale.range();
            let domain = colorScale.domain();
            this.patternSegments = range.map((color: string, index: number) => {
                return new PatternSegment(color, index/range.length, (index+1)/range.length);
            });
            this.gradientStops = null;
            this.bins = domain.map((val: string, index: number) => {
                let count = values.filter((other) => other === val).length;
                return new Bin(
                    val,
                    this.plotAreaWidth * index/domain.length,
                    this.plotAreaWidth * (index+1)/domain.length,
                    count,
                    range[index] as string,
                    val === null);
            });
            // this.yMax will be max count, expressed as a percentage, rounded up to 5%
            let yMax = d3.max(this.bins, (bin) => bin.count);
            yMax = 100 * yMax / this.totalCount;
            this.yMax = Math.ceil((yMax + .1)/5) * 5;
            // prepare to scale counts to heights
            this.yScale = d3.scale.linear()
                .domain([0, this.yMax * this.totalCount / 100]) // compensate for rounded y-max
                .range([this.plotAreaHeight, 0]);
            // create two data points per bin
            // array of points, where each point is [x, y]
            let points: [number, number][] = [];
            this.bins.forEach((bin) => {
                points.push([bin.xMin, this.yScale(bin.count)]);
                points.push([bin.xMax, this.yScale(bin.count)]);
            });
            this.path = d3.svg.line().interpolate("linear")(points);
        } else {
            // TODO TBD
        }
    }
    setCurrentBin(bin: Bin, event: MouseEvent): void {
        this.currentBin = bin;
        let targetRect = (<any> event.target).getBoundingClientRect();
        this.popoverTop = window.pageYOffset + targetRect.top +
            (targetRect.bottom - targetRect.top)/2 - 20;
        this.popoverLeft = window.pageXOffset + targetRect.right;
    }
    getMissingValueBin(): Bin {
        let lastBin = this.bins[this.bins.length - 1];
        return (lastBin.isMissingValue ? lastBin : null);
    }
}

export class GradientStop {
    constructor(
        public color: string,
        public offset: string) {
    }
}

class PatternSegment {
    constructor(
        public color: string,
        public start: number,
        public width: number) {
    }
}

class Bin {
    constructor(
        public label: string,
        public xMin: number,
        public xMax: number,
        public count: number,
        public color: string,
        public isMissingValue: boolean) {
        if (isMissingValue) {
            this.label = "missing value";
        }
    }
    getWidth(): number {
        return this.xMax - this.xMin;
    }
}