/// <reference path="../../typings/d3/d3.d.ts" />
import {Component, OnInit, EventEmitter, Output} from '@angular/core';

@Component ({
    moduleId: module.id,
    selector: 'abundance-slider',
    template: `
    <svg id="target"></svg>
    <span class="slider-value">{{percentage}}%</span>
    `,
    styleUrls: ['./RelativeAbundanceComponent.css']
})

export class AbundanceSlider implements OnInit{
    class = 'relative';
    
    percentage: number = 50;
    
    @Output()
    radiusChanges: EventEmitter<number> = new EventEmitter<number>();
    
    ngOnInit() {
        var svg = d3.select("#target").attr("width", 210).attr("height", 12);
        
        /**
        * Originally based upon https://jsfiddle.net/md61de9d/9/, modified to suit ARI visual analytics design
        */
        function mySlider() : any {
            var _update = function(v: any) {
                value = v;
            }; // General update function that updates the value
            var xScale: any; // Scale for the x-axis
            var brush: any; // Brush which is used to represent the slider
            var slider: any = {}; // The slider control that will be returned  
            // The following properties are public and modified through the getter/setter functions
            var margin = {
                top: 0,
                left: 0,
                bottom: 0,
                right: 0
            };
            var cssClass = '';
            var width = 200;
            var minimumValue = 0;
            var maximumValue = 100;
            var value = 0;
            var handleRadius = 5;
            // The following functions are public and modified through the getter/setter functions
            var _callback = function(slider: any, v: any) {};
            var _databindCallback = function(slider: any, v: any) {};
            /**
             * Changes the width of the slider (pre initialization only)
             * @param {number} The width that the slider should take
             * @return {number} The width that the slider should take or the slider
             */
            slider.width = function(_: any) {
                if (!arguments.length) return width;
                width = _;
                return slider;
            };
            /**
             * Changes the radius of the slider handle (pre initialization only)
             * @param {number} The radius of the slider handle
             * @return {number} The radius of the slider handle or the slider
             */
            slider.handleRadius = function(_: any) {
                if (!arguments.length) return handleRadius;
                handleRadius = _;
                return slider;
            };
            /**
             * Changes the minimum value of the slider (pre initialization only)
             * @param {number} The minimum value that the slider can take
             * @return {number} The minimum value that the slider can take or the slider
             */
            slider.minimumValue = function(_: any) {
                if (!arguments.length) return minimumValue;
                minimumValue = _;
                return slider;
            };
            /**
             * Changes the maximum value of the slider (pre initialization only)
             * @param {number} The maximum value that the slider can take
             * @return {number} The maximum value that the slider can take or the slider
             */
            slider.maximumValue = function(_: any) {
                if (!arguments.length) return maximumValue;
                maximumValue = _;
                return slider;
            };
            /**
             * Changes the margin of the slider (pre initialization only)
             * @param {object} The margin that the slider should use
             * @return {number} The margin that the slider is using or the slider
             */
            slider.margin = function(_: any) {
                if (!arguments.length) return margin;
                margin = _;
                return slider;
            };
            /**
             * Changes the custom CSS class that should be attatched to the slider (pre initialization only)
             * @param {string} The custom CSS class of the slider
             * @return {string} The current custom CSS class of the slider or the slider
             */
            slider.cssClass = function(_: any) {
                if (!arguments.length) return cssClass;
                cssClass = _;
                return slider;
            };
            /**
             * Changes the current value of the slider
             * @param {number} The current value of the slider
             * @return {number} The current value of the slider or the slider
             */
            slider.value = function(_: any) {
                if (!arguments.length) return value;
                _update(_);
                return slider;
            };
            /**
             * Changes the callback of the slider, triggered when the value changes
             * @param {function} The function to call that can take up to 2 parameters (slider, value)
             * @return {function} The current callback function
             */
            slider.callback = function(_: any) {
                if (!arguments.length) return _callback;
                _callback = _;
                return slider;
            };
            /**
             * When the slider changes it's value by having the slider dragged
             * then calculate the new value and trigger an update/callback
             */
            function brushed() {
                // if this is not a programmatic event
                if ((<any>d3.event).sourceEvent) {
                    // determine the value from the mouse position and the scale
                    var v: any = xScale.invert(d3.mouse(this)[0]);
                    // trigger an update of the value and a callback if the 
                    // value has changed - which throttles the updates when
                    // the slider has hit the min/max value
                    if (v !== value) {
                        _update(v);
                        _callback(slider, v);
                        _databindCallback(slider, v);
                    }
                }
            };
            /**
             * Configures the slider based on the given JavaScript object
             * which makes configuring a slider from JSON much simpler.
             * @param {object} A JavaScript object of properties
             * @return {object} The slider for method chaining
             */
            slider.configure = function(config: any) {
                // ensure that we don't have an empty object
                config = config || {};
                if (config.width) {
                    slider.width(config.width);
                }
                if (config.minimumValue) {
                    slider.minimumValue(config.minimumValue);
                }
                if (config.maximumValue) {
                    slider.maximumValue(config.maximumValue);
                }
                if (config.value) {
                    slider.value(config.value);
                }
                if (config.cssClass) {
                    slider.cssClass(config.cssClass);
                }
                if (config.handleRadius) {
                    slider.handleRadius(config.handleRadius);
                }
                if (config.margin) {
                    slider.margin(config.margin);
                }
                return slider;
            };
            /**
             * Appends the slider to the DOM underneath the given target
             * @param {selector} Either a D3 object or a string selector to locate the DOM element to insert into. Must be an SVG element, or child of an SVG element
             * @return {object} The slider for method chaining
             */
            slider.appendTo = function() {
                // Convert the target into a valid D3 selection
                // that we can append to
                // Set the scale for the x-axis and restrict it to the given values
                xScale = d3.scale.linear().domain([minimumValue, maximumValue]).range([0, width]).clamp(true);
                // Setup a brush that covers the given scale, when that brush
                // changes trigger the brushed function
                brush = d3.svg.brush().x(xScale).extent([0, 0]).on("brush", brushed);
                // Create the 3 bars used to represent a slider
                var sliderBar = svg.append("g").attr("class", "slider " + cssClass).attr("transform", "translate(" + margin.left + ", " + margin.top + ")").call(d3.svg.axis().scale(xScale).tickSize(0) // ensure that end ticks are not displayed
                        .ticks([])) // ensure that no ticks are included in the DOM
                    .select(".domain") // this is a custom class added by D3
                    .select(function() {
                        return this.parentNode.appendChild(this.cloneNode(true));
                    }).attr("class", "inner-bar").select(function() {
                        return this.parentNode.appendChild(this.cloneNode(true));
                    }).attr("class", "fill-bar");
                // Create the slider group
                var slide = svg.append("g").attr("class", "slider " + cssClass).attr("transform", "translate(" + margin.left + ", " + margin.top + ")").call(brush);
                // Create the slider handle
                var handle = slide.append("circle").attr("class", "handle").attr("r", handleRadius);
                // Extend the update function to do some extra interesting things
                _update = function(val) {
                    // Update the brush position
                    brush.extent([val, val]);
                    value = brush.extent()[0];
                    // Move the slider handle to the correct location
                    handle.attr("cx", xScale(value));
                    // Move the filled bar to the slider location by modifying the path
                    sliderBar.attr("d", "M0,0V0H" + xScale(value) + "V0");
                    sliderBar.attr("data-bind", "value: " + xScale(value))
                };
                // Update to the initial value
                _update(value);
                return slider;
            };
        
            slider.prototype = Object.prototype; // set prototype inheritance
            return slider;
        }
        
        var slider = mySlider().configure({
            minimumValue: 0,
            maximumValue: 1,
            value: 0.5
        }).margin({
            top: 5,
            left: 5
        }).appendTo().callback( (context: any, value: any) => {
            this.percentage = Math.round(context.value() * 100);
            this.radiusChanges.emit(this.percentage);
        });
    }
    
}