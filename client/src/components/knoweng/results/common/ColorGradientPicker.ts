import {Component, Input, Output, EventEmitter} from '@angular/core';
import {DomSanitizer, SafeStyle} from '@angular/platform-browser';

@Component({
    moduleId: module.id,
    selector: 'color-gradient-picker',
    templateUrl: './ColorGradientPicker.html',
    styleUrls: ['./ColorGradientPicker.css']
})
export class ColorGradientPicker {
    class = 'relative';
    
    //Following is the list of available gradients from https://projects.invisionapp.com/d/#/console/11370914/299450252/inspect
    
    //MIDPOINT
    static MIDPOINT_1 = ['#B54839', '#E4C676', '#144671']; // default one
    static MIDPOINT_2 = ['#B54839', '#B54839', '#B54839', '#B54839', '#B54839', '#FCFBFB', '#144671', '#144671', '#144671', '#144671', '#144671']; // first and last 40%
    static MIDPOINT_3 = ['#B33724', '#000000', '#128055'];
    //1-COLOR GRADIENT
    static ONE_COLOR_1 = ['#8AE7FF', '#2C87A2', '#143E4A'];
    static ONE_COLOR_2 = ['#F1593F', '#A23B2A', '#4A1B13'];
    static ONE_COLOR_3 = ['#C3FFD8', '#5AA072', '#1E5431'];
    static ONE_COLOR_4 = ['#C9D4DD', '#6A7781', '#33424D'];
    //2-COLOR GRADIENT
    static BI_COLOR_1 = ['#E56325', '#C9693B', '#AC6C4E', '#8C6F5F', '#656F70', '#266F80'];
    static BI_COLOR_2 = ['#DCD77C', '#BCC17E', '#9CAC80', '#7B9781', '#578381', '#266F80'];
    static BI_COLOR_3 = ['#80DD87', '#305167'];
    //3-COLOR GRADIENT
    static TRI_COLOR_1 = ['#FFE38A', '#65D475', '#20689E']; //default two
    static TRI_COLOR_2 = ['#FFE38A', '#AC6C4E', '#266F80'];
    static TRI_COLOR_3 = ['#80DD87', '#81DFC7', '#305167'];
    //FULL SPECTRUM
    static FULL_SPECTRUM = ['#B54839', '#E1753A', '#DBC842', '#64A957', '#397A9E', '#4B3BA8'];
    
    static DEFAULT_ONE_COLOR_GRADIENT = ColorGradientPicker.getDefaultGradientScale(ColorGradientPicker.TRI_COLOR_1);
    static DEFAULT_TWO_COLORS_GRADIENT = ColorGradientPicker.getDefaultGradientScale(ColorGradientPicker.MIDPOINT_1);
    
    static getDefaultGradientScale(gradients: string[]) {
        let divisor = gradients.length - 1;
        return d3.scale.linear<string>().domain(gradients.map((val: string, index: number) => index/divisor)).range(gradients);
    }
    
    gradientsGroups: GradientsGroup[] = [
        { 
            groupName: 'MIDPOINT',
            gradients:  [
                        ColorGradientPicker.MIDPOINT_1,
                        ColorGradientPicker.MIDPOINT_2,
                        ColorGradientPicker.MIDPOINT_3
                        ]
        },
        {
            groupName: '1-COLOR GRADIENT',
            gradients:  [
                            ColorGradientPicker.ONE_COLOR_1,
                            ColorGradientPicker.ONE_COLOR_2,
                            ColorGradientPicker.ONE_COLOR_3,
                            ColorGradientPicker.ONE_COLOR_4
                        ]
        },
        {
            groupName: '2-COLOR GRADIENT',
            gradients: [
                            ColorGradientPicker.BI_COLOR_1,
                            ColorGradientPicker.BI_COLOR_2,
                            ColorGradientPicker.BI_COLOR_3
                        ]
        },
        {
            groupName: '3-COLOR GRADIENT',
            gradients: [
                            ColorGradientPicker.TRI_COLOR_1,
                            ColorGradientPicker.TRI_COLOR_2,
                            ColorGradientPicker.TRI_COLOR_3
                        ]
        },
        {
            groupName: 'FULL SPECTRUM',
            gradients: [
                            ColorGradientPicker.FULL_SPECTRUM
                        ]
        }
    ];
    
    @Output()
    changeTo: EventEmitter<any> = new EventEmitter<any>();
    
    @Input()
    currentGradientScale: any;
    
    constructor(private _sanitizer: DomSanitizer) {
    }
    
    /**
     * notify host(parent) component when user clicks on one in the dropdown list of gradient choices
     */
    selectGradientScale(groupIndex: number, gradientIndex: number): any {
        let group: GradientsGroup = this.gradientsGroups[groupIndex];
        let gradient: string[] = group.gradients[gradientIndex];
        let divisor = gradient.length - 1;
        let scale = d3.scale.linear<string>().domain(gradient.map((val: string, index: number) => index/divisor)).range(gradient);
        this.changeTo.emit(scale);
    }
    
    /**
     * Help function that converts one of the above constant gradient color code strings into CSS
     */ 
    getGradientStyle(groupIndex: number, gradientIndex: number): SafeStyle {
        let group: GradientsGroup = this.gradientsGroups[groupIndex];
        let gradient: string[] = group.gradients[gradientIndex];
        let divisor = gradient.length - 1;
        let scale = d3.scale.linear<string>().domain(gradient.map((val: string, index: number) => index/divisor)).range(gradient);
        let domain = scale.domain();
        let range = scale.range();
        return this._sanitizer.bypassSecurityTrustStyle("linear-gradient(90deg, " +
            range.map((color: string, i: number) => color + " " + (100*domain[i]) + "%").join(", ") +
        ")");
    }
    
    /**
     * Help function to convert d3.scale to gradient CSS 
     */ 
    convertScaleToGradientStyle(scale: any): SafeStyle {
        let domain = scale.domain();
        let range = scale.range();
        return this._sanitizer.bypassSecurityTrustStyle("linear-gradient(90deg, " +
            range.map((color: string, i: number) => color + " " + (100*domain[i]) + "%").join(", ") + ")");
    }
    
    
}

interface GradientsGroup {
    groupName: string;
    gradients: string[][];
}