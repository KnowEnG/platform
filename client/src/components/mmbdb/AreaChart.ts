//This file is to draw one or more area chart(s) using cohort(s) data (diversity, abundance etc.), with possible a stick (with or without a rectangle top) to represent individual patient data. 

import {Component, AfterViewInit, Input, ElementRef, ViewChild} from '@angular/core';

@Component ({
    moduleId: module.id,
    selector: "area-chart",
    template: '<div #svgHost></div>',
    styleUrls: ['./CohortComparisonTool.css']
})

export class AreaChart implements AfterViewInit {
  class = 'relative';
    
    @Input()
    data: CohortDataRecord[];
    
    @Input()
    configOptions: AreaChartConfigOptions;
    
    @ViewChild("svgHost") svgHost: ElementRef;
    
    ngAfterViewInit(): void {
        var localShowAxes = (this.configOptions.showAxes === undefined) ? false : this.configOptions.showAxes;
        var localShowBubble = (this.configOptions.showBubble === undefined) ? false : this.configOptions.showBubble;
        var localMargin = (this.configOptions.margin === undefined) ? 0 : this.configOptions.margin;
        var margin = {
            top: localMargin,
            right: localMargin,
            bottom: localMargin,
            left: localMargin
        },
        realWidth = this.configOptions.width - margin.left - margin.right,
        realHeight = this.configOptions.height - margin.top - margin.bottom;

         // get the native element to contain our svg
        var nativeElement: any = this.svgHost.nativeElement;
        var svg = d3.select(nativeElement).append("svg")
            .attr("width", this.configOptions.width)
            .attr("height", this.configOptions.height);

        var cohorts: any[] = [];
        var charts: any[] = [];
        
        var dataLength = this.data.length;
        //find maxXDataPoint
        var maxXDataPoint = this.configOptions.maxX;
        
        //find maxYDataPoint
        var maxYDataPoint = this.configOptions.maxY;
        var showAxes = localShowAxes;
        var showBubble = localShowBubble;

      
        /* Loop through and get each cohort name and push it into an array to use later */
        for (i = 0; i < dataLength; i++) {
          cohorts.push(this.data[i].cohortName);
        }

        var cohortsCount = cohorts.length;

        for (var i = 0; i < dataLength; i++) {
          this.drawChart({
            chartData: this.data[i].points,
            id: i,
            name: this.data[i].cohortName,
            width: realWidth,
            height: realHeight,
            maxXDataPoint: maxXDataPoint,
            maxYDataPoint: maxYDataPoint,
            svg: svg,
            margin: margin,
            showAxes: (i == 0) && showAxes,
            showBubble: showBubble
        });
      }
    }
  
    drawChart(options: any): void {
      var chartData: AreaChartGraphPoint[] = <AreaChartGraphPoint[]> options.chartData;
      var width = options.width;
      var height = options.height;
      var maxXDataPoint = options.maxXDataPoint;
      var maxYDataPoint = options.maxYDataPoint;
      var svg = options.svg;
      var id = options.id;
      var name = options.name;
      var margin = options.margin;
      var showAxes = options.showAxes;
      var showBubble = options.showBubble;

      /* XScale is linear based on maxXDataPoint*/
      var xScale = d3.scale.linear()
        .range([0, width])
        .domain([0, maxXDataPoint]);

      /* YScale is linear based on the maxYDataPoint */
      var yScale = d3.scale.linear()
        .range([height, 0])
        .domain([0, maxYDataPoint]);
      
      /* 
        This is what creates the chart.
        There are a number of interpolation options. 
        'basis' smooths it the most, however, when working with a lot of data, this will slow it down 
      */
      var area = d3.svg.area()
        .interpolate("basis")
        .x(function(d: any) {
          return xScale(d.xValue);
        })
        .y0(height)
        .y1(function(d: any) {
          return yScale(d.yValue);
        });

      /*
        Assign it a class so we can assign a fill color
        And position it on the page
      */
      var chartContainer = svg.append("g")
        .attr('class', name.toLowerCase())
        .attr("transform", "translate(" + margin.left + "," + margin.top + ")");


      /* We've created everything, let's actually add it to the page */
      if (name.toLowerCase() == "baseline") {
        chartContainer.append("path")
          .data([chartData])
          .attr("class", "chart")
          .attr("clip-path", "url(#clip-" + id + ")")
          .attr("d", area)
          .attr("fill", "#c5b9a6")
          .attr("fill-opacity", 0.5);
      }
      else if (name.toLowerCase() == "cohort 1") {
        chartContainer.append("path")
          .data([chartData])
          .attr("class", "chart")
          .attr("clip-path", "url(#clip-" + id + ")")
          .attr("d", area)
          .attr("fill", "#88a7cc")
          .attr("fill-opacity", 0.5);
      }
      else {
        //draw a simple staight line
        chartContainer.append("line")
          .attr("x1", xScale(chartData[0].xValue))
          .attr("y1", yScale(0))
          .attr("x2", xScale(chartData[0].xValue))
          .attr("y2", yScale(chartData[0].yValue))
          .attr("stroke", "#96b570")
          .attr("stroke-width", 2);
        
        if (showBubble) {
          // add the bubble to the group
          chartContainer.append("rect")
            .attr("x", xScale(chartData[0].xValue) - 20)
            .attr("y", yScale(chartData[0].yValue))
            .attr("height", 20)
            .attr("width", 40)
            .attr("fill", "#96b570");
            // add the count text to the group
          chartContainer.append("text")
            .attr("x", xScale(chartData[0].xValue))
            .attr("y", yScale(chartData[0].yValue) + 14)
            .text(chartData[0].xValue)
            .attr("text-anchor", "middle")
            .attr("font-family", "'Lato', sans-serif")
            .attr("font-size", "14px")
            .attr("fill", "#ffffff");
        }
      }

      var xAxis = d3.svg.axis().scale(xScale).orient("bottom").ticks(2);
      var yAxis = d3.svg.axis().scale(yScale).orient("right").ticks(2);
      /* Only want axes on the last cohort*/
      if (showAxes) {
        chartContainer.append("g")
          .attr("class", "x axis")
          .attr("transform", "translate(0," + width + ")")
          .attr("stroke", "#BEBCBD")
          .attr("fill", "none")
          .attr("stroke-width", "1px")
          .call(xAxis);

        chartContainer.append("g")
          .attr("class", "y axis")
          .attr("transform", "translate(-15,0)")
          .attr("stroke", "#BEBCBD")
          .attr("fill", "none")
          .attr("stroke-width", "1px")
          .call(yAxis);
      }
    }
}
    

export class AreaChartConfigOptions {
    
    //maximum value draw on X-axis
    maxX: number;
    
    //maximum value draw on Y-axis
    maxY: number;
    
    //width of svg element that holds the area chart
    width: number;
    
    //height of svg element
    height: number;
    
    //wether to show axes or not on the chart graph
    showAxes: boolean;
    
    //margin between svg element and the gragh
    margin: number;
    
    //show bubble on the candle stick top for the individual
    showBubble: boolean;
    
    constructor( margin: number, maxX: number, maxY: number, width: number, height: number, showAxes: boolean, showBubble: boolean) {
      this.margin = margin;
      this.maxX = maxX;
      this.maxY = maxY;
      this.width = width;
      this.height = height;
      this.showAxes = showAxes;
      this.showBubble = showBubble;
    }
    
}

export interface CohortDataRecord {
    
    cohortName: string;
    
    //in pairs such as {200, 0,8}, {20, 12.5) etc.
    points: AreaChartGraphPoint[];
}

export interface AreaChartGraphPoint {
    
    //OTU number
    xValue: number;
    
    //Could be abundance percentage, richness or evenness
    yValue: number;
}