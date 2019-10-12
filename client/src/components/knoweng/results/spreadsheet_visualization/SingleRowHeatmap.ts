import {Component, OnChanges, SimpleChange, Input} from '@angular/core';
import {TypeaheadMatch} from 'ngx-bootstrap';

import {CategoricRow, Row, RowStateRequest, Spreadsheet, SSVState} from '../../../../models/knoweng/results/SpreadsheetVisualization';
import {CellHeatmapEvent} from '../common/CellHeatmap';
import {GradientStop} from './MiniDistributionGraph';
import {SelectableRowData} from './SelectableTypes';
import {SurvivalCohort, SurvivalObservation} from './SurvivalCurvesPlot';

import {FileService} from '../../../../services/knoweng/FileService';
import {SpreadsheetVisualizationService} from '../../../../services/knoweng/SpreadsheetVisualizationService';

import {NumberFormatPipe} from '../../../../pipes/knoweng/NumberFormatPipe';

@Component({
    moduleId: module.id,
    selector: 'single-row-heatmap',
    templateUrl: './SingleRowHeatmap.html',
    styleUrls: ['./SingleRowHeatmap.css']
})

export class SingleRowHeatmap implements OnChanges {
    class = 'relative';

    @Input()
    width: number;

    @Input()
    height: number;

    @Input()
    row: SelectableRowData;

    @Input()
    displayedHeatmapData: number[];

    @Input()
    state: SSVState;

    showRollover: boolean = false;
    rolloverTop: number = null;
    rolloverLeft: number = null;

    showTimeToEventPopup: boolean = false;
    timeToEventPopupTop: number = null;
    timeToEventPopupLeft: number = null;
    timeToEventMaxRowsForSelect = 15;
    // TODO: migrate all components to reactive forms? sure would help this
    // component
    timeToEventFormModel = {
        spreadsheetOptions: [] as {name: string, index: number}[],
        eventSpreadsheetIndex: null as string, // string b/c directly from form
        timeSpreadsheetIndex: null as string, // string b/c directly from form
        eventRowFilter: "",
        timeRowFilter: "",
        eventRowOptions: [] as string[],
        timeRowOptions: [] as string[],
        eventRowIndex: null as number, // number b/c from typeahead callback
        timeRowIndex: null as number, // number b/c from typeahead callback
        eventValueOptions: [] as string[],
        eventValue: null as string,
        isDone: false
    };
    timeToEventPValue = null as number;

    rlcInfo: RolloverLeftCategoricInfo = null;
    rlnInfo: RolloverLeftNumericInfo = null;
    rrInfo: RolloverRightInfo = null;

    totalCount: number = null;

    highlightBin: HistoBin = null;
    tooltipTop: number = null;
    tooltipLeft: number = null;
    tooltipIsLabel = false; // otherwise is sample count

    /**
     * In rollover, height of the plots--"matched" because left plot and right
     * heights will be matched.
     */
    plotMatchedHeight = 0;

    survivalCohorts: SurvivalCohort[] = [];

    // receiving numFormatter from ng dependency injection; need to pass it to
    // RolloverLeftNumericInfo constructor
    constructor(
        private _numFormatter: NumberFormatPipe,
        private _fileService: FileService,
        private _ssvService: SpreadsheetVisualizationService) {
    }
    ngOnChanges(changes: {[propertyName: string]: SimpleChange}) {
        // TODO: be more selective about the changes we respond to
        if (this.row && this.row.getRawRow() && this.row.getColorScale()) {
            this.calculateLayout();
        }
        if (this.state) {
            this.timeToEventFormModel.spreadsheetOptions = this.state.spreadsheets.map((ss, idx) => {
                let file = this._fileService.getFileByIdSync(ss.fileId);
                let name = "Unknown deleted file";
                if (file) {
                    name = file.filename;
                }
                return {name: name, index: idx};
            });
            this.setEventValueOptions();
            this.prepareTimeToEventData();
        }
    }
    setEventValueOptions(): void {
        let eventRow = this.state.timeToEventEventRow;
        if (eventRow) {
            let unsortedDistinctValues = Array.from((new Set(eventRow.getValuesOrderedBySampleNames())).values());
            this.timeToEventFormModel.eventValueOptions = unsortedDistinctValues.sort((valA, valB) => {
                return Row.compareValues(valA, valB, true);
            }).filter((val) => val !== null); // not allowing MV as the event state--could, with some care, but hearing it's not worthwhile
        } else {
            this.timeToEventFormModel.eventValueOptions = [];
        }
    }
    calculateLayout(): void {
        this.totalCount = this.row.getRawRow().getValuesOrderedBySampleNames().length;
        switch(this.row.getType()) {
            case 'numeric': {
                this.rlcInfo = null;
                this.rlnInfo = new RolloverLeftNumericInfo(this.row, this._numFormatter);
                this.rrInfo = new RolloverRightInfo(
                    this.row, this.state.columnGroupingRow, this.rlnInfo.bins);
                this.plotMatchedHeight = Math.max(
                    this.rlnInfo.getHeight(), this.rrInfo.getHeight());
                break;
            }
            case 'categoric': {
                this.rlcInfo = new RolloverLeftCategoricInfo(this.row);
                this.rlnInfo = null;
                this.rrInfo = new RolloverRightInfo(
                    this.row, this.state.columnGroupingRow, this.rlcInfo.bins);
                this.plotMatchedHeight = Math.max(
                    this.rlcInfo.getHeight(), this.rrInfo.getHeight());
                break;
            }
            default: {
                // TODO TBD
            }
        }
    }
    prepareTimeToEventData(): void {
        let timeRow = this.state.timeToEventTimeRow;
        let eventRow = this.state.timeToEventEventRow;
        let eventValue = this.state.stateRequest.timeToEventEventValue;
        if (this.timeToEventFormModel.isDone && this.rlcInfo && timeRow && eventRow && eventValue) {
            let timeValues = timeRow.getValuesOrderedBySampleNames();
            let eventValues = eventRow.getValuesOrderedBySampleNames();
            this.survivalCohorts = this.rlcInfo.bins.filter((bin) => !bin.isMissingValue).map((bin) => {
                let observations = [] as SurvivalObservation[];
                bin.sampleIndexSet.forEach((i) => {
                    if (timeValues[i] !== null) {
                        observations.push(new SurvivalObservation(
                            timeValues[i], eventValues[i] + "" == eventValue));
                    }
                });
                return new SurvivalCohort(bin.label, bin.color, observations);
            });
        } else {
            this.survivalCohorts = null;
        }
        this.timeToEventPValue = this.getPValueFromState();
    }
    getRowStateRequestForThisRow(): RowStateRequest {
        return new RowStateRequest(this.row.spreadsheet.spreadsheetId, this.row.rowIdx);
    }
    getPValueFromState(): number {
        let thisRowRequest = this.getRowStateRequestForThisRow();
        let pvals = this.state.timeToEventPvals.filter((item) => {
            return RowStateRequest.equal(item.request, thisRowRequest);
        });
        let returnVal = null as number;
        if (pvals.length == 1) {
            returnVal = pvals[0].pval;
        }
        return returnVal;
    }
    onCellClicked(selection: CellHeatmapEvent): void {
        this.showRollover = true;
        this.rolloverTop = selection.event.pageY;
        this.rolloverLeft = selection.event.pageX;
    }
    onCloseRollover(): void {
        this.showRollover = false;
    }
    getPopupWidth(): number {
        return this.timeToEventFormModel.isDone ? 1028 : 450;
    }
    onTimeToEventButtonClicked(event: MouseEvent): void {
        this.showTimeToEventPopup = true;
        this.timeToEventPopupTop = event.pageY;
        this.timeToEventPopupLeft = event.pageX;
        // pre-populate the form with any time-to-event data previously configured
        let isDone = true;
        if (this.state.timeToEventEventRow) {
            this.timeToEventFormModel.eventRowFilter = this.state.timeToEventEventRow.getName();
            this.timeToEventFormModel.eventRowIndex =
                this.state.spreadsheets.findIndex((ss) => {
                    return ss.spreadsheetId == this.state.timeToEventEventRow.spreadsheet.spreadsheetId;
                });
            this.setEventValueOptions();
            if (this.state.timeToEventEventValue) {
                this.timeToEventFormModel.eventValue = this.state.timeToEventEventValue;
            } else {
                isDone = false;
            }
        } else {
            isDone = false;
        }
        if (this.state.timeToEventTimeRow) {
            this.timeToEventFormModel.timeRowFilter = this.state.timeToEventTimeRow.getName();
            this.timeToEventFormModel.timeRowIndex =
                this.state.spreadsheets.findIndex((ss) => {
                    return ss.spreadsheetId == this.state.timeToEventTimeRow.spreadsheet.spreadsheetId;
                });
        } else {
            isDone = false;
        }
        if (isDone) {
            this.onTimeToEventFormDone();
        } else {
            this.onReturnToForm();
        }
    }
    onTimeToEventFormDone(): void {
        this.timeToEventFormModel.isDone = true;
        let pval = this.getPValueFromState();
        if (pval === null) {
            let stateRequest = this.state.stateRequest.copy();
            let thisRowRequest = this.getRowStateRequestForThisRow();
            stateRequest.timeToEventPvalRequests = [
                ...stateRequest.timeToEventPvalRequests, thisRowRequest];
            this._ssvService.updateSSVState(stateRequest);
        }
        this.prepareTimeToEventData();
    }
    onCloseTimeToEventPopup(): void {
        this.showTimeToEventPopup = false;
    }
    onChangeEventSpreadsheetIndex(): void {
        // clear previous value for event row and event value
        this.timeToEventFormModel.eventRowFilter = "";
        this.timeToEventFormModel.eventRowIndex = null;
        this.timeToEventFormModel.eventValueOptions = [];
        this.timeToEventFormModel.eventValue = null;
        // set the options for the event row
        let spreadsheet = this.getSpreadsheetFromIdString(
            this.timeToEventFormModel.eventSpreadsheetIndex);
        this.timeToEventFormModel.eventRowOptions = spreadsheet.rowNames;
    }
    onChangeTimeSpreadsheetIndex(): void {
        // clear previous value for time row
        this.timeToEventFormModel.timeRowFilter = "";
        this.timeToEventFormModel.timeRowIndex = null;
        // set the options for the time row--require numeric
        let spreadsheet = this.getSpreadsheetFromIdString(
            this.timeToEventFormModel.timeSpreadsheetIndex);
        this.timeToEventFormModel.timeRowOptions = spreadsheet.rowNames.filter((name, idx) => {
            return spreadsheet.rowTypes[idx] == "numeric";
        });
    }
    onEventRowKeyup(): void {
        // make sure form is incomplete so Done is disabled
        this.timeToEventFormModel.eventRowIndex = null;
        this.timeToEventFormModel.eventValue = null;
    }
    onTimeRowKeyup(): void {
        // make sure form is incomplete so Done is disabled
        this.timeToEventFormModel.timeRowIndex = null;
    }
    onChangeEventRowIndex(): void {
        // called from template and from onChangeEventRow
        let spreadsheet = this.getSpreadsheetFromIdString(
            this.timeToEventFormModel.eventSpreadsheetIndex);
        let stateRequest = this.state.stateRequest.copy();
        stateRequest.timeToEventEventRowRequest = new RowStateRequest(
            spreadsheet.spreadsheetId, this.timeToEventFormModel.eventRowIndex);
        this._ssvService.updateSSVState(stateRequest);
    }
    onChangeEventRow(event: TypeaheadMatch): void {
        let spreadsheet = this.getSpreadsheetFromIdString(
            this.timeToEventFormModel.eventSpreadsheetIndex);
        this.timeToEventFormModel.eventRowIndex = this.getIndexForRow(
            spreadsheet, event.item);
        this.onChangeEventRowIndex();
    }
    getSpreadsheetFromIdString(spreadsheetIdString: string): Spreadsheet {
        return this.state.spreadsheets[parseInt(spreadsheetIdString)];
    }
    getIndexForRow(spreadsheet: Spreadsheet, rowName: string): number {
        return spreadsheet.rowNames.indexOf(rowName);
    }
    onChangeTimeRowIndex(): void {
        // called from template and from onChangeTimeRow
        let spreadsheet = this.getSpreadsheetFromIdString(
            this.timeToEventFormModel.timeSpreadsheetIndex);
        let stateRequest = this.state.stateRequest.copy();
        stateRequest.timeToEventTimeRowRequest = new RowStateRequest(
            spreadsheet.spreadsheetId, this.timeToEventFormModel.timeRowIndex);
        this._ssvService.updateSSVState(stateRequest);
    }
    // wouldn't be hard to share one handler between the select-based case and
    // the typeahead-based case, but the typeahead contract is different in
    // the latest ng-bootstrap, and this ensures the compiler will call attention
    // here during upgrade
    onChangeTimeRow(event: TypeaheadMatch): void {
        let spreadsheet = this.getSpreadsheetFromIdString(
            this.timeToEventFormModel.timeSpreadsheetIndex);
        this.timeToEventFormModel.timeRowIndex = this.getIndexForRow(
            spreadsheet, event.item);
        this.onChangeTimeRowIndex();
    }
    onChangeEventValue(): void {
        let stateRequest = this.state.stateRequest.copy();
        stateRequest.timeToEventEventValue = this.timeToEventFormModel.eventValue;
        this._ssvService.updateSSVState(stateRequest);
    }
    onReturnToForm(): void {
        this.timeToEventFormModel.isDone = false;
    }
    setHighlightBin(bin: HistoBin, event: MouseEvent, isLabel = false): void {
        this.highlightBin = bin;
        this.tooltipIsLabel = isLabel;
        let targetRect = (<any> event.target).getBoundingClientRect();
        this.tooltipTop = targetRect.bottom;
        this.tooltipLeft = -40 + // 40 is half the tooltip's width
            .5*(targetRect.left + targetRect.right);
    }
}

/**
 * Represents a single histogram bin in the left-side categoric plot
 * or the right-side grouping plot of the rollover.
 */
class HistoBin {
    constructor(
        public label: string,
        public color: string,
        public sampleIndexSet: Set<number>,
        public isMissingValue: boolean) {
        this.enforceMissingValueName(); // doing it this way to avoid super() trouble
    }
    enforceMissingValueName(): void {
        if (this.isMissingValue) {
            this.label = "Missing Values (MV)";
        }
    }
    getCount(): number {
        return this.sampleIndexSet.size;
    }
}

/**
 * Represents a single histogram bin in the left-side numeric plot.
 * These bins are subdivided.
 */
class SubdividedHistoBin extends HistoBin {
    constructor(
        public label: string,
        public color: string,
        public sampleIndexSet: Set<number>,
        public isMissingValue: boolean,
        public subBinCounts: number[],
        public labelColor: string) {
        super(label, color, sampleIndexSet, isMissingValue);
        this.enforceMissingValueName();
    }
}

/**
 * Represents a group on the right-side plot of the rollover.
 */
class Group {
    constructor(
        public label: string,
        public count: number,
        public bins: HistoBin[],
        public isMissingValue: boolean) {
        if (isMissingValue) {
            this.label = "Missing Values (MV)";
        }
    }
}

class RolloverLeftCategoricInfo {
    /* width of left portion, for histogram labels. */
    leftWidth = 210;
    /* width of right potion, for histogram bars. */
    rightWidth = 179;
    /* height of top portion, for ticks and labels. */
    headerHeight = 20;
    /* header baseline, measured in pixels from top of header area. */
    headerBaseline = 13;
    /* empty vertical space below last bin. */
    marginBottom = 5;
    /* height of tick. */
    tickHeight = 4;
    /* pixels between start of right portion and the 0% tick. */
    scaleLeftMargin = 7;
    /* pixels between the histoMax tick and the end of the right portion. */
    scaleRightMargin = 22;
    /* height of one bin, not including the stroke (1px top, 1px bottom). */
    binHeight = 12;
    /* height of the <g> associated with one HistoBin. */
    groupHeight = 20;
    /* the bins. */
    bins: HistoBin[] = null;
    /* linear scale from count fraction to x position. */
    xScale: any = null; // d3 doesn't export Linear<number, number>
    /* max observed count fraction, rounded up to a nice number. */
    histoMax: number;
    constructor(row: SelectableRowData) {
        let values = row.getRawRow().getValuesOrderedBySampleNames() as string[];
        let colorScale = row.getColorScale() as d3.scale.Ordinal<string, {}>;
        let range = colorScale.range();
        let domain = colorScale.domain();
        this.bins = domain.map((val: string, index: number) => {
            let sampleIndexSet = new Set<number>();
            values.forEach((other, otherIndex) => {
                if (other == val) {
                    sampleIndexSet.add(otherIndex);
                }
            });
            return new HistoBin(
                val,
                range[index] as string,
                sampleIndexSet,
                val === null);
        });
        let scaleStart = this.leftWidth + this.scaleLeftMargin;
        let scaleEnd = scaleStart +
            (this.rightWidth - this.scaleLeftMargin - this.scaleRightMargin);
        let maxPercentage = d3.max(this.bins, (bin) => bin.getCount()) / values.length;
        // set this.histoMax to maxPercentage, rounded up to the nearest 10%
        this.histoMax = 10 * Math.ceil((100*maxPercentage + .1) / 10) / 100;
        this.xScale = d3.scale.linear()
            .domain([0, this.histoMax])
            .range([scaleStart, scaleEnd]);
    }
    getHeight(): number {
        return this.headerHeight + this.marginBottom +
            (this.bins ? this.bins.length * this.groupHeight : 0);
    }
}

class RolloverLeftNumericInfo {
    /* space before first header row. */
    marginTop = 3;
    /* height of each header row (there are two). */
    headerHeight = 16;
    /* space after each header row. */
    headerMarginBottom = 2;
    /* header stroke width. */
    headerStrokeWidth = 1;
    /* horizontal rule (there are two) thickness. */
    hrHeight = 1;
    /* height of main graph area. */
    graphHeight = 86;
    /* vertical space between top of graph area and top of clamp, equal to
     * vertical space between bottom of clamp and bottom of graph area. */
    graphTopBottomPadding = 2;
    /* space above color bar. */
    colorBarMarginTop = 2;
    /* height of color bar. */
    colorBarHeight = 14;
    /* space after color bar. */
    marginBottom = 5;
    /* the width of the area containing the labels. */
    labelAreaWidth = 81;
    /* the distance between the left edge of the svg and the "[" shape next to the y axis. */
    clampMarginLeft = 69;
    /* the width of the clamp. */
    clampWidth = 5;
    /* the width of each normal bin (there are five). */
    normalBinWidth = 56;
    /* the space right of each normal bin. */
    normalBinMarginRight = 1;
    /* the width of the missing-value bin (there is always one). */
    mvBinWidth = 21;
    /* the space right of the missing-value bin. */
    mvBinMarginRight = 4;
    /* number of normal bins. */
    numNormalBins = 5;
    /* number of subbins per normal bin. */
    numSubBinsPerBin = 14;
    /* the bins. */
    bins: SubdividedHistoBin[];
    /* max value on y-scale, which corresponds to max sub-bin count rounded up to a nice number. */
    histoMax = 0;
    /* linear scale from sub-bin count to y position. */
    yScale: any; // d3 doesn't export Linear<number, number>
    /* path for curve. */
    curve: string;
    /* unique ID for svg gradient def. */
    patternId: string;
    /* gradient stops for svg gradient def. */
    gradientStops: GradientStop[];
    /* min value on x axis. */
    xMin: number;
    /* max value on x axis. */
    xMax: number;
    constructor(row: SelectableRowData, numFormatter: NumberFormatPipe) {

        let values = row.getRawRow().getValuesOrderedBySampleNames() as number[];
        let colorScale = row.getColorScale() as d3.scale.Linear<string, string>;
        let range = colorScale.range();
        let colorScaleDomain = colorScale.domain();
        // SelectableRowData color scale operates on normalized values; TODO change?
        this.xMin = (row.getValueRange() as number[])[0];
        this.xMax = (row.getValueRange() as number[])[1];
        let percentScale = d3.scale.linear().domain([this.xMin, this.xMax]).range([0, 1]);

        // separate the missing values from the non-missing values
        // attach indices to non-missing (i.e., populated) values so we can get
        // what we need from d3 functions
        let missingValueIndices = new Set<number>();
        let populatedValues: {index: number, value: number}[] = [];
        values.forEach((val: number, index: number) => {
            if (val === null) {
                missingValueIndices.add(index);
            } else {
                populatedValues.push({index: index, value: val});
            }
        });

        // determine primary bins
        let primaryBins = d3.layout.histogram<{index: number, value: number}>()
            .bins(this.numNormalBins)
            .value((d: {index: number, value: number}) => d.value)(populatedValues);
        this.bins = primaryBins.map((d3bin) => {
            let sampleIndexSet = new Set<number>();
            d3bin.forEach((item) => {
                sampleIndexSet.add(item.index);
            });
            let subBins = d3.layout.histogram<{index: number, value: number}>()
                .bins(this.numSubBinsPerBin)
                .value((d: {index: number, value: number}) => d.value)(d3bin);
            let color = colorScale(percentScale(d3bin.x + .5*d3bin.dx));
            // use lightness of color to determine label color
            // light colors get dark labels and vice versa
            let hsl = d3.rgb(color).hsl();
            let labelColor = hsl.l >  0.5 ? "#29465F" : "#FFFFFF";
            return new SubdividedHistoBin(
                numFormatter.transform(d3bin.x) + "-" + numFormatter.transform(d3bin.x + d3bin.dx),
                color,
                sampleIndexSet,
                false,
                subBins.map((subBin) => subBin.y),
                labelColor);
        });
        this.bins.push(new SubdividedHistoBin(
            null,
            "#FFFFFF",
            missingValueIndices,
            true,
            [missingValueIndices.size], // one sub-bin for MV
            "#29465F"));
        let maxSubBinCount = d3.max(this.bins, (bin) => {
            return d3.max(bin.subBinCounts);
        });
        // set this.histoMax to maxSubBinCount, rounded up to the nearest 10
        this.histoMax = 10 * Math.ceil((maxSubBinCount + .1) / 10);
        this.yScale = d3.scale.linear()
            .domain([0, this.histoMax])
            .range([1, this.graphHeight]);
        // path across normal bins
        // don't include MV--that'd suggest a continuity with the normal domain
        // all x values are relative to the left edge of the svg
        // all y values are relative to the top edge of the graph area
        let points: [number, number][] = [];
        let subBinWidth = this.getSubBinWidth(this.bins[0]);
        this.bins.forEach((bin, binIndex, bArray) => {
            if (!bin.isMissingValue) {
                let startX = this.getBinX(bin, binIndex);
                bin.subBinCounts.forEach((count, subBinIndex, sbArray) => {
                    let offsetX = subBinWidth * subBinIndex;
                    // use right edge for last bin, else middle
                    if (subBinIndex == sbArray.length-1 && binIndex == bArray.length-1) {
                        offsetX += subBinWidth;
                    } else {
                        offsetX += subBinWidth/2;
                    }
                    points.push([startX + offsetX, this.graphHeight - this.yScale(count)]);
                });
            }
        });
        this.curve = d3.svg.line().interpolate("basis")(points);

        // prepare color bar
        // need a unique id for the svg def
        this.patternId = "pattern" + Math.random().toString().substring(2);
        this.gradientStops = range.map((color: string, index: number) => {
            return new GradientStop(color, 100*colorScaleDomain[index] + "%");
        });
    }
    getBinX(bin: SubdividedHistoBin, index: number): number {
        return this.labelAreaWidth + index * (this.normalBinWidth + this.normalBinMarginRight);
    }
    getSubBinWidth(bin: SubdividedHistoBin): number {
        return (bin.isMissingValue ? this.mvBinWidth : this.normalBinWidth)/bin.subBinCounts.length;
    }
    getColorBarWidth(): number {
        return this.numNormalBins * this.normalBinWidth +
            (this.numNormalBins - 1) * this.normalBinMarginRight;
    }
    getWidth(): number {
        return this.labelAreaWidth +
            this.numNormalBins * (this.normalBinWidth + this.normalBinMarginRight) +
            this.mvBinWidth + this.mvBinMarginRight;
    }
    getHeight(): number {
        return this.marginTop + 2*(this.headerHeight + this.headerMarginBottom) +
            2*this.hrHeight + this.graphHeight + this.colorBarMarginTop +
            this.colorBarHeight + this.marginBottom;
    }
}

class RolloverRightInfo {
    /* width of left portion, for histogram bars. */
    leftWidth = 170;
    /* width of right portion, for histogram labels. */
    rightWidth = 219;
    /* distance from start of right portion to start of sample count text. */
    secondaryLabelOffset = 130; // TODO dynamic positioning based on longest (truncated) group label?
    /* pixels between start of left portion and histoMax tick. */
    scaleLeftMargin = 5;
    /* pixels between 0% tick and start of right portion. */
    scaleRightMargin = 7;
    /* height of top portion, for ticks and labels. */
    headerHeight = 20;
    /* header baseline, measured in pixels from top of header area. */
    headerBaseline = 13;
    /* height of tick. */
    tickHeight = 4;
    /* empty height before a bin. */
    binMarginTop = 1;
    /* height of one bin in the normal (not highlighted) state, not including stroke of 1px on top and 1px on bottom. */
    binHeightNormal = 2;
    /* height of one bin in the highlighted state, not including stroke of 1px on top and 1px on bottom. */
    binHeightHighlight = 4;
    /* stroke width for bin */
    binStroke = 1;
    /* empty height at end of group. */
    groupMarginBottom = 7;
    /* valid values: "normal", "self", null. */
    groupingType: string;
    /* the groups. */
    groups: Group[];
    /* linear scale from count to x position. */
    xScale: any = null; // d3 doesn't export Linear<number, number>
    /* max observed bin-level count, rounded up to a nice number. */
    histoMax: number;
    constructor(
            thisRow: SelectableRowData,
            groupingRow: CategoricRow,
            ungroupedBins: HistoBin[]) {
        if (groupingRow) {
            if (!Row.equal(groupingRow, thisRow.getRawRow())) {
                this.groupingType = "normal";
                // determine sample indices per group
                this.groups = [];
                let currentGroupVal: string = undefined;
                let currentGroupSampleIndices: Set<number> = undefined;
                let groupVals = groupingRow.getValuesOrderedBySampleNames();
                groupVals.forEach((groupVal, index) => {
                    // if this marks the end of the last group in progress,
                    // handle the last group and start new group in progress
                    if (groupVal !== currentGroupVal) {
                        // create a Group for the group in progress, unless this is
                        // index 0, in which case there is no group in progress
                        if (index != 0) {
                            this.groups.push(new Group(
                                currentGroupVal,
                                currentGroupSampleIndices.size,
                                RolloverRightInfo.binsForGroup(ungroupedBins, currentGroupSampleIndices),
                                currentGroupVal === null
                            ));
                        }
                        // start a new group in progress
                        currentGroupVal = groupVal;
                        currentGroupSampleIndices = new Set<number>();
                    }
                    currentGroupSampleIndices.add(index);
                    // if this is the last sample, wrap up the group in progress
                    if (index == groupVals.length - 1) {
                        this.groups.push(new Group(
                            groupVal,
                            currentGroupSampleIndices.size,
                            RolloverRightInfo.binsForGroup(ungroupedBins, currentGroupSampleIndices),
                            groupVal === null
                        ));
                    }
                });
                let scaleStart = this.scaleLeftMargin;
                let scaleEnd = this.leftWidth - this.scaleRightMargin;
                let maxCount = d3.max(this.groups, (group) => {
                    return d3.max(group.bins, (bin) => bin.getCount());
                });
                // set this.histoMax to maxCount, rounded up to the nearest 10
                this.histoMax = 10 * Math.ceil((maxCount + .1) / 10);
                // note this scale maps smaller values to bigger x vals
                this.xScale = d3.scale.linear()
                    .domain([this.histoMax, 0])
                    .range([scaleStart, scaleEnd]);
            } else {
                this.groupingType = "self";
            }
        } else {
            this.groupingType = null;
        }
    }
    getHeight(): number {
        return this.headerHeight +
            (this.groups ? this.groups.length * this.getGroupHeight() : 0);
    }
    getGroupHeight(): number {
        let returnVal = this.groupMarginBottom;
        if (this.groups && this.groups[0] && this.groups[0].bins) {
            returnVal += this.groups[0].bins.length * (this.binMarginTop + this.binHeightNormal + 2*this.binStroke);
        }
        return returnVal;
    }
    getBinStrokeColor(bin: HistoBin, highlightBin: HistoBin): string {
        let returnVal = bin.color;
        if (bin === highlightBin) {
            returnVal = '#000000';
        } else if (bin.isMissingValue) {
            returnVal = '#C7C7C7';
        }
        return returnVal;
    }
    getBinX(bin: HistoBin): number {
        // this handles the problem of the minimum width
        return this.xScale(0) - this.getBinWidth(bin);
    }
    getBinWidth(bin: HistoBin): number {
        let returnVal = this.xScale(0) - this.xScale(bin.getCount());
        return Math.max(returnVal, 1); // enfore minimum width
    }
    getBinY(bin: HistoBin, highlightBin: HistoBin, binIndex: number): number {
        // first, skip past any bins above this one in the group
        // note layout is determined by binHeightNormal, not binHeightHighlight
        // (highlight case uses same layout and introduces overlap)
        let returnVal = binIndex * (this.binMarginTop + this.binHeightNormal + 2*this.binStroke);
        // now move down to the start of the <rect>
        returnVal += this.binMarginTop + this.binStroke;
        // if this is the highlight bin, vertically center the larger bin over the normal bin
        if (bin === highlightBin) {
            returnVal += (this.binHeightNormal - this.binHeightHighlight)/2;
        }
        return returnVal;
    }
    getBinHeight(bin: HistoBin, highlightBin: HistoBin) {
        return (bin === highlightBin ? this.binHeightHighlight : this.binHeightNormal);
    }
    static binsForGroup(ungroupedBins: HistoBin[], sampleIndicesForGroup: Set<number>): HistoBin[] {
        return ungroupedBins.map((bin) => {
            let intersection = new Set<number>();
            // ts compiler doesn't like some js interator syntax, so doing this
            // this old fashioned way
            let binIndices = Array.from(bin.sampleIndexSet.values());
            binIndices.forEach((index) => {
                if (sampleIndicesForGroup.has(index)) {
                    intersection.add(index);
                }
            });
            return new HistoBin(
                bin.label,
                bin.color,
                intersection,
                bin.isMissingValue
            );
        });
    }
}
