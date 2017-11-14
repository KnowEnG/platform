import {Component, Input, OnChanges, SimpleChange} from '@angular/core';
import {RadarConfigOptions} from './RelativeAbundanceComponent';

@Component ({
    moduleId: module.id,
    selector: "radarchart",
    templateUrl: './RadarChart.html',
    styleUrls: ['./RadarChart.css']
})

export class RadarChart implements OnChanges{
    class = 'relative';
    
    /**
     * The input data for radar chart consists multiple groups' data. Each group is visualized as polygon in the radar chart.
     */
    @Input()
    data: Array<RadarChartGroupDataRecord>;

    @Input()
    configOption: RadarConfigOptions;
    
    allAxis: Array<string>;
    
    maxValue: number = 50;
    
    /**
     * cohort and CSS color class mapping
     */
    cohortCSSClassDictionary: {[cohortName: string]: string} = {
        'baseline': 'baseline baseline-stroke',
        'cohort 1': 'cohort1 cohort1-stroke',
        'individual': 'individual individual-stroke'
    };
    
    ngOnChanges(changes: {[propertyName: string]: SimpleChange}) {
        this.allAxis = [];
        for (var i = 0; i < this.data[0].axes.length; i++) {
            this.allAxis.push(this.data[0].axes[i].axis);
        }
        // adjust max percentage represented by axis
        this.maxValue = Math.max(this.configOption.maxValue, d3.max(this.data, function(d) {
            return d3.max(d.axes, function(o) { return o.value; });
        }));
    } 
    
    /**
     * Radar chart circle radius
     */
    circleRadius(width: number, height: number): number {
        return Math.min(width/2, height/2);
    }
    
    /**
     * End of axis's X coordinate
     */
    axisEndingX(width: number, index: number, axisCount: number): number {
        return width / 2 * (1 - Math.sin(index * 2 * Math.PI / axisCount));
    }
    
    /**
     * End of axis's Y coordinate
     */
    axisEndingY(height: number, index: number, axisCount: number): number {
        return height / 2 * (1 - Math.cos(index * 2 * Math.PI / axisCount));
    }
    
    /**
     * axis label X coordinate
     */
    axisLabelX(width: number, index: number, axisCount: number): number {
        return  width / 2 * (1 - 1.3 * Math.sin(index * 2 * Math.PI / axisCount));
    }
    
    /**
     * axis label Y coordinate
     */
    axisLabelY(height: number, index: number, axisCount: number): number {
        return height / 2 * (1 - 1.1 * Math.cos(index * 2 * Math.PI / axisCount));
    }
    
    /**
     *  Generate the data format for svg polygon points 
     */
    getGroupPoints(groupDataRecord: RadarChartGroupDataRecord, width: number, height: number, axesCount: number): string {
        var verticesString = "";
        var max = this.maxValue;
        groupDataRecord.axes.forEach(function(d, i) { 
            var xCoordinate =  width / 2 * (1 - (Math.max(d.value, 0) / max) * Math.sin(i * 2 * Math.PI / axesCount));
            var yCoordinate = height / 2 * (1 - (Math.max(d.value, 0) / max) * Math.cos(i * 2 * Math.PI / axesCount));
            verticesString += xCoordinate + "," + yCoordinate + " "; 
        });
        return verticesString;
    }
    
    /**
     * Get the css class name which generally has the color code for a polygon, and a general class name which is used in mouse event handler.
     */ 
    getGroupCSSClassNames(groupDataRecord: RadarChartGroupDataRecord): string {
        return this.cohortCSSClassDictionary[groupDataRecord.group] + " polygon-areas";
    }
    
    /**
     * When mouse is over a polygon, highlight it
     */
    highlightPolygonArea(event: Event) {
        d3.selectAll(".polygon-areas") // fade all other polygons out
            .transition()
            .duration(250)
            .attr("fill-opacity", 0.1)
            .attr("stroke-opacity", 0.1);
        d3.select(event.target) // focus on active polygon
            .transition()
            .duration(250)
            .attr("fill-opacity", 0.7)
            .attr("stroke-opacity", 1 );
    }
    
    /**
     * When mouse moves away, restore orginal polygons
     */
    dehighlightPolygonArea(event: Event) {
        d3.selectAll(".polygon-areas")
            .transition()
            .duration(250)
            .attr("fill-opacity", 0.3)
            .attr("stroke-opacity", 1);
    }
}

export class RadarChartGroupDataRecord {
    group: string;
    axes: Array<RadarChartAxisDataRecord>;
}

export class RadarChartAxisDataRecord {
    axis: string;
    value: number;
}