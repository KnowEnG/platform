import {AfterViewInit, Component, ElementRef, Input, ViewChild, ViewEncapsulation} from '@angular/core';
import {ThresholdPickerService} from '../../services/common/ThresholdPickerService';

/**
 * This is a d3 area graph with a few twists:
 * 1. There's a threshold-slider the user can drag left and right to designate
 *    a subset of the input data as "included." These changes are streamed via
 *    the ThresholdPickerService. In the DOM, the threshold-slider is an SVG
 *    group consisting of a line and a shape on top (ellipse or rect for now)
 *    containing `numIncluded` as a text label. A d3 drag behavior is associated
 *    with the threshold-slider group.
 * 2. The plot area--i.e., the region bounded by the curve, the x-axis, and the
 *    left and right sides of the svg--is filled not with a solid color but with
 *    an SVG pattern. The pattern is constructed such that the area left of the
 *    threshold-slider is one color, and the area right of the threshold-slider
 *    is another color. (There's also a corresponding pattern for the background
 *    of the plot area, in case the left and right sides of the background need
 *    different colors, too.
 * 3. The user can rescale the x-axis with a dropdown. Specify the options and
 *    the initial value using `scales` and `currentScale`.
 */

@Component({
    moduleId: module.id,
    selector: 'threshold-picker',
    encapsulation: ViewEncapsulation.Emulated, // ensures we can use hostElementAttribute for styling; see below
    styleUrls: ['./ThresholdPicker.css'],
    // The `path.area` and `rect.area` fill styles here tie the area plot and
    // its background to patterns that are defined within the class. They should
    // not be overridden with other CSS rules.
    //
    // Instead, to change the fill color of the area plot and its background,
    // create CSS rules that specify fill colors for the following:
    // - `.foreground.included`, the area plot left of the threshold-slider
    // - `.foreground.excluded`, the area plot right of the threshold-slider
    // - `.background.included`, the background left of the threshold-slider
    // - `.background.excluded`, the background right of the threshold-slider
    styles: [`
        path.area {
            fill: url(#pathPattern)
        }`,`
        rect.area {
            fill: url(#rectPattern)
        }`
    ],
    template: `<div #svgHost></div>`
})

export class ThresholdPicker implements AfterViewInit {
    class = 'relative';

    /**
     * Sorted array of scores providing the y-axis values for the plot. The
     * x-axis value for each element is simply the element's index in this
     * array.
     * The user will move a slider to adjust the `numIncluded`, which is the
     * number of elements in this array whose index is less than the threshold.
     *
     * TODO developer-friendly validation here and elsewhere, instead of relying
     * on ng2 exceptions and mangled plots
     */
    @Input()
    sortedValues: number[];

    /**
     * Array of scales to offer in the x-axis scale selector. Pass an array
     * with only one element to disable the scale selector.
     */
    @Input()
    scales: number[];

    /**
     * The current scale from `scales`. This value must be found in `scales`.
     */
    @Input()
    currentScale: number;

    /**
     * Shape to use for the threshold-slider bubble. Must be "ellipse" or
     * "rect".
     */
    @Input()
    bubbleShape: string;

    /**
     * Total height of this component in pixels.
     * TODO would be pretty easy to eliminate height/width/margins as inputs
     * and instead let the host declare them with CSS styles, which we could
     * interrogate. A few advantages to that approach. Main disadvantage is it'd
     * be less clear to hosts that h/w/margins need to be specified.
     */
    @Input()
    totalHeight: number;

    /**
     * Total width of this component in pixels.
     */
    @Input()
    totalWidth: number;

    /**
     * Margin in pixels between top of component and top of plot area. Needs to
     * accommodate threshold bubble.
     */
    @Input()
    marginTop: number;

    /**
     * Margin in pixels between bottom of plot area and bottom of component.
     * Needs to accommodate x-axis labels and dropdown.
     */
    @Input()
    marginBottom: number;

    /**
     * Margin in pixels between right edge of plot area and right edge of
     * component. Needs to accommodate x-axis labels, dropdown, and threshold
     * bubble.
     */
    marginRight: number = 30;

    /**
     * Margin in pixels between left edge of component and left edge of plot
     * area. Needs to accommodate y-axis labels and threshold bubble.
     */
    marginLeft: number = 25;

    /**
     * Number of pixels the threshold-slider should extend above the top of the
     * plot area.
     */
    @Input()
    sliderSpilloverTop: number;

    /**
     * Number of pixels the threshold-slider should extend below the bottom of
     * the plot area.
     */
    @Input()
    sliderSpilloverBottom: number;

    /**
     * Number included, which determines the position of the threshold line;
     * it'll be positioned so that `numIncluded` elements of the
     * `sortedValues` array appear to its left.
     *
     * TODO subscribe and respond to ThresholdPickerService changes
     */
    numIncluded: number;

    /** linear scale mapping rank to x coordinate. */
    xScale: any;

    /** linear scale mapping importance to y coordinate. */
    yScale: any;

    /** the x-axis generator. */
    xAxis: any;

    /** the svg group containing the x-axis elements. */
    gXAxis: any;

    /** the area-plot generator. */
    area: any;

    /** the area plot svg path. */
    areaPath: any;

    /** the scale `select` element. */
    scaleSelect: any;

    /** svg group containing threshold-slider elements. */
    thresholdGroup: any;

    /** svg text containing `numIncluded` count. */
    thresholdBubbleText: any;

    /**
     * fill pattern elements for coloring the path and its background according
     * to the current threshold-slider position
     */
    plotFills: PlotFills;

    /** reference to the template element that'll contain the svg element. */
    @ViewChild('svgHost') svgHost: ElementRef;

    /**
     * The host element attribute Angular assigns to our instantiated view,
     * uniquely identifying it for ViewEncapsulation.Emulated. By applying the
     * same attribute to DOM elements injected by d3, we can use styles from
     * styleUrls on d3 content, too.
     */
    hostElementAttribute: string = null;

    constructor(public _thresholdPickerService: ThresholdPickerService) {
        this.numIncluded = this._thresholdPickerService.numIncludedStream.getValue();
    }

    /**
     * Creates the DOM elements, plots the user's data, and sets up handlers for
     * drag events.
     * TODO decompose this class into several classes
     */
    ngAfterViewInit(): void {

        var plotWidth: number = this.totalWidth - this.marginLeft - this.marginRight;
        var plotHeight: number = this.totalHeight - this.marginTop - this.marginBottom;

        // get the native element to contain our svg
        var nativeElement: any = this.svgHost.nativeElement;

        // get ng2's "host element attribute" assigned to our component; it'll
        // allow us to apply css styles from styleUrls to DOM nodes inserted by
        // d3
        // TODO accomplish this with ng2 APIs
        // TODO factor out this behavior
        var elementAttributes: any = nativeElement.attributes;
        for (var i=0; i < elementAttributes.length; i++) {
            var attrName: string = elementAttributes.item(i).name;
            if (attrName.startsWith("_ngcontent")) {
                this.hostElementAttribute = attrName;
                break;
            }
        }
        if (null === this.hostElementAttribute) {
            alert("Couldn't find host element attribute for threshold picker. Contact technical support.");
        }

        // add the svg element to the DOM
        var svg: any = d3.select(nativeElement).append("svg")
            .attr("width", this.totalWidth)
            .attr("height", this.totalHeight);

        // this should happen before any other content is added to the svg
        this.definePlotFills(svg);

        // create a group to contain everything else, translated according to the margins
        var topGroup: any = svg.append("g")
            .attr("transform", "translate(" + this.marginLeft + "," + this.marginTop + ")");

        // map the array of scores into an array of (rank, importance) pairs
        var chartData = this.prepareData();

        // create the x scale and x-axis group
        this.xScale = this.defineXScale(chartData, plotWidth);
        this.defineXAxisGroup(topGroup, plotHeight, plotWidth);

        // create the y scale and y-axis group group
        this.yScale = this.defineYScale(chartData, plotHeight);
        this.defineYAxisGroup(topGroup, plotHeight);

        // add a background to the plot area
        topGroup.append("rect")
            .attr("class", "area")
            .attr("width", plotWidth+4)
            .attr("height", plotHeight+4)
            .attr("y", -2)
            .attr("x", -2);

        this.definePlotPath(topGroup, chartData, plotHeight);
        this.defineThresholdSlider(topGroup, plotHeight);

        // update the fills according to the current threshold
        this.updatePlotFills(this.xScale(this.numIncluded));
        // update the threshold-slider position according to the current threshold
        this.updateThresholdSlider(this.xScale(this.numIncluded));

        // allow css styles on all the svg elements
        svg.selectAll('*')
            .attr(this.hostElementAttribute, "");
    }
    /**
     * Prepares data for plotting, subject to the current scale.
     */
    prepareData(): Array<any> {
        return this.sortedValues
            .slice(0, this.currentScale)
            .map(function(d: number, idx: number) {
                return {rank: idx, importance: d};
            });
     }
    /**
     * Creates the svg path for the area graph.
     */
    definePlotPath(topGroup: any, chartData: Array<any>, plotHeight: number): void {
        // create the area-plot generator
        this.area = d3.svg.area()
            .x((d: any) => this.xScale(d.rank))
            .y0(plotHeight)
            .y1((d: any) => this.yScale(d.importance));

        // plot the data
        this.areaPath = topGroup.append("path")
            .datum(chartData)
            .attr("class", "area")
            .attr("d", this.area);
    }
    /**
     * Creates a `defs` block defining the patters for the plot path and its
     * rectangle background.
     */
    definePlotFills(svg: any): void {
        // initialize the PlotFills object
        this.plotFills = new PlotFills();

        // add a defs block to contain the path and background fills
        var defs = svg.append("defs");

        // add a pattern for the plot path
        var pathPattern = defs.append("pattern")
            .attr("id", "pathPattern")
            .attr("x", 0) // no x-offset
            .attr("y", 0) // no y-offset
            .attr("width", 1) // 100% of the object we're filling (don't repeat)
            .attr("height", 1) // 100% of the object we're filling (don't repeat)
            .attr("patternContentUnits", "objectBoundingBox"); // use the same coordinate system on the rect children of this pattern
        // this rectangle will fill the portion left of the threshold-slider
        // note: for all these rects, don't bother setting things that depend on
        // the threshold-slider position; we'll call updatePlotFills later to
        // keep it DRY
        this.plotFills.pathLeft = pathPattern.append("rect")
            .attr("class", "foreground included")
            .attr("x", 0)
            .attr("y", 0)
            .attr("height", 1);
        // this rectangle will fill the portion right of the threshold-slider
        this.plotFills.pathRight = pathPattern.append("rect")
            .attr("class", "foreground excluded")
            .attr("y", 0)
            .attr("height", 1);

        // add a pattern for the rectange background
        var rectPattern = defs.append("pattern")
            .attr("id", "rectPattern")
            .attr("x", 0) // no x-offset
            .attr("y", 0) // no y-offset
            .attr("width", 1) // 100% of the object we're filling (don't repeat)
            .attr("height", 1) // 100% of the object we're filling (don't repeat)
            .attr("patternContentUnits", "objectBoundingBox"); // use the same coordinate system on the rect children of this pattern
        // this rectangle will fill the portion left of the threshold-slider
        this.plotFills.rectLeft = rectPattern.append("rect")
            .attr("class", "background included")
            .attr("x", 0)
            .attr("y", 0)
            .attr("height", 1);
        // this rectangle will fill the portion right of the threshold-slider
        this.plotFills.rectRight = rectPattern.append("rect")
            .attr("class", "background excluded")
            .attr("y", 0)
            .attr("height", 1);
    }
    /**
     * Creates the threshold-slider elements.
     */
    defineThresholdSlider(topGroup: any, plotHeight: number): void {
        // add a group to contain the threshold-slider elements
        // note: not setting the x position here; we'll call
        // updateThresholdSlider later
        this.thresholdGroup = topGroup.append("g")
            .attr("class", "threshold");
        // add the line to the group
        this.thresholdGroup.append("line")
            .attr("x1", 0)
            .attr("y1", 0 - this.sliderSpilloverTop)
            .attr("x2", 0)
            .attr("y2", plotHeight + this.sliderSpilloverBottom);
        // add the bubble to the group
        var maxTextBBox: any = this.getMaxBubbleTextBBox();
        if (this.bubbleShape == "ellipse") {
            this.thresholdGroup.append("ellipse")
                .attr("cx", 0)
                .attr("cy", 0 - this.sliderSpilloverTop)
                .attr("rx", maxTextBBox.width/2 + 3)
                .attr("ry", maxTextBBox.height/2 + 3);
        } else if (this.bubbleShape == "rect") {
            this.thresholdGroup.append("rect")
                .attr("rx", 5)
                .attr("ry", 5)
                .attr("x", 0 - maxTextBBox.width/2 - 3)
                .attr("y", 0 - this.sliderSpilloverTop - maxTextBBox.height/2 - 3)
                .attr("height", maxTextBBox.width + 6)
                .attr("width", maxTextBBox.height + 6);
        }
        // add the count text to the group
        this.thresholdBubbleText = this.thresholdGroup
            .append("text")
            .attr("x", 0)
            .attr("y", 4 - this.sliderSpilloverTop)
            .text(this.numIncluded);

        // define drag behaviors
        var drag: any = d3.behavior.drag()
            .on("drag", () => this.onThresholdDrag())
            .on("dragend", () => this.onThresholdDragEnd());

        // respond to drag events on the thresholdGroup
        this.thresholdGroup.call(drag);
    }
    /**
     * Creates a linear scale for the x coordinates.
     */
    defineXScale(chartData: Array<any>, plotWidth: number): any {
        return d3.scale.linear()
            .range([0, plotWidth])
            .domain(d3.extent(chartData, function(d: any) { return d.rank; }));
    }
    /**
     * Creates the x-axis group.
     */
    defineXAxisGroup(topGroup: any, plotHeight: number, plotWidth: number): void {
        // add a group element to contain the x-axis and labels
        this.gXAxis = topGroup.append("g")
            .attr("class", "x axis")
            .attr("transform", "translate(0," + plotHeight + ")");

        // create the x-axis
        this.xAxis = d3.svg.axis()
            .scale(this.xScale)
            .ticks(0)
            .orient("bottom");

        // add the x-axis to the group
        this.gXAxis.call(this.xAxis);

        // add the labels to the group
        this.gXAxis
            .append("text")
            .attr("y", 23)
            .attr("x", 0)
            .text("0");

        if (this.scales.length > 1) {
            // add the scale-select widget
            var foWidth: number = 70;
            this.scaleSelect = this.gXAxis
                .append("foreignObject")
                .attr("y", 10)
                .attr("x", plotWidth + this.marginRight - foWidth)
                .attr("width", foWidth)
                .attr("height", 20)
                .append("xhtml:select");

            // add options to the scale-select widget
            this.scaleSelect.selectAll("option")
                .data(this.scales)
                .enter().append("xhtml:option")
                .attr("value", (d: any) => d)
                .property("selected", (d: any) => (d == this.currentScale ? 1 : 0))
                .html(function(d: any) {return d;});

            // listen for scale changes
            this.scaleSelect.on("change", ()=> this.onScaleChange());
        } else {
            this.gXAxis
                .append("text")
                .attr("y", 23)
                .attr("x", plotWidth)
                .text(this.scales[0]);
        }
    }
    /**
     * Creates a linear scale for the y coordinates.
     */
    defineYScale(chartData: Array<any>, plotHeight: number): any {
        return d3.scale.linear()
            .range([plotHeight, 0])
            .domain([0, 1.08*d3.max(chartData, function(d: any) { return d.importance; })]);
    }
    /**
     * Creates the y-axis group.
     */
    defineYAxisGroup(topGroup: any, plotHeight: number): void {
        // add a group element to contain the y-axis and labels
        var gYAxis: any = topGroup.append("g")
            .attr("class", "y axis");

        // create the y-axis
        var yAxis = d3.svg.axis()
            .scale(this.yScale)
            .ticks(0)
            .orient("left");

        // add the y-axis to the group
        gYAxis.call(yAxis);

        // calculate y positions for the + and - labels at the ends of the y-axis
        var yPlus: number = 3;
        var yMinus: number = plotHeight + 5;

        // add the labels to the group
        gYAxis
            .append("text")
            .attr("class", "label")
            .attr("transform", "rotate(-90)")
            .attr("y", -6)
            .attr("x", (yPlus - yMinus)/2)
            // TODO: move the y-axis label text to parameter?
            .text("Importance");
        gYAxis
            .append("text")
            .attr("class", "minmax")
            .attr("y", yPlus)
            .attr("x", -12)
            .text("+");
        gYAxis
            .append("text")
            .attr("class", "minmax")
            .attr("y", yMinus)
            .attr("x", -12)
            .text("–"); // note: en dash, not minus sign
    }
    /**
     * Updates the fill pattern for the area plot according to the threshold
     * position.
     */
    updatePlotFills(newX: number): void {
        var fraction = newX / this.xScale.range()[1];

        this.plotFills.pathLeft
            .attr("width", fraction);

        this.plotFills.pathRight
            .attr("x", fraction)
            .attr("width", 1-fraction);

        this.plotFills.rectLeft
            .attr("width", fraction);

        this.plotFills.rectRight
            .attr("x", fraction)
            .attr("width", 1-fraction);
    }
    /**
     * Updates the position of the threshold-slider.
     */
    updateThresholdSlider(newX: number): void {
        // relocate line and bubble
        this.thresholdGroup
            .attr("transform", "translate(" + newX + ", 0)");
    }
    /**
     * Handles a change in the x-scale.
     */
    onScaleChange(): void {
        // update the scale
        this.currentScale = parseInt(this.scaleSelect.property("value"), 10);

        // prepare the data and scales
        var chartData: Array<any> = this.prepareData();
        this.xScale.domain(d3.extent(chartData, function(d: any) { return d.rank; }));

        // TODO transitions (i.e., animations) for these? made a couple of quick
        // attempts but not worth the trouble at this point

        // update the x-axis (not bothering with y-axis for now)
        this.gXAxis.call(this.xAxis);

        // update the plot
        this.areaPath.datum(chartData).attr("d", this.area);

        // clamp the threshold, if necessary
        var newX: number = this.xScale(this.numIncluded);
        if (this.numIncluded > this.currentScale) {
            this.numIncluded = this.currentScale;
            this.thresholdBubbleText.text(this.numIncluded);
            newX = this.xScale.range()[1];
        }

        // update the fills according to the current threshold
        this.updatePlotFills(newX);
        // update the threshold-slider position according to the current threshold
        this.updateThresholdSlider(newX);
    }
    /**
     * Handles a change in the drag position while the drag is still in
     * progress.
     */
    onThresholdDrag(): void {

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

        // update the threshold-slider position and fills
        this.updateThresholdSlider(newX);
        this.updatePlotFills(newX);

        // determine new number included
        // note we use ceiling here because x-values correspond to 0-based array
        // indices but we want a count of the number of elements included
        var newIncluded: number = Math.ceil(this.xScale.invert(newX));
        // if threshold-slider is all the way right...
        if (newX == range[1]) {
            // consider all elements included
            newIncluded++;
        }

        // update bubble text
        if (newIncluded != this.numIncluded) {
            this.numIncluded = newIncluded;
            this.thresholdBubbleText.text(this.numIncluded);
        }
    }
    /**
     * Handles the completion of a drag.
     */
    onThresholdDragEnd(): void {
        // trigger event
        this._thresholdPickerService.numIncludedStream.next(this.numIncluded);
    }
    /**
     * Returns the maximum width of the bubble text.
     */
    getMaxBubbleTextBBox(): any {
        var maxDigits: number = this.numIncluded.toString().length;
        var testString = Array(maxDigits+1).join("0"); // a string of maxDigits zeros
        var tempText = this.thresholdGroup
            .append("text")
            .text(testString);
        var returnVal: any = tempText.node().getBBox();
        tempText.remove();
        return returnVal;
    }
}

/**
 * Contains the rectangles that compose the fill patterns for the plot path and
 * its rectangle background.
 */
class PlotFills {
    // the portion of the plot path left of the threshold-slider
    pathLeft: any;
    // the portion of the plot path right of the threshold-slider
    pathRight: any;
    // the portion of the rectangle background left of the threshold-slider
    rectLeft: any;
    // the portion of the rectangle background right of the threshold-slider
    rectRight: any;
}

