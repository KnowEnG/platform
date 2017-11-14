/// <reference path="../../typings/d3/d3.d.ts" />
import {Component, Input, OnChanges, SimpleChange} from '@angular/core';

@Component ({
    selector: 'abundance-topotu',
    template: `
        <span #svgHost>
            <svg [attr.width]="width" [attr.height]="height" style="margin-bottom: -4px">
                <g [attr.transform]="'translate(' + width/2 + ',' + height/2 + ')'">
                    <ellipse cx="0" cy="0" [attr.rx]="getRx()" ry="8.5" style="fill: #e05869"/>
                    <text x="0" y="3.5" text-anchor="middle" style="font-family: 'Lato', sans-serif; font-weight: 700; font-size: 10px; fill: #ffffff">{{ topOTUCount }}</text>
                </g>
            </svg>
        </span>
    `
})

/**
 * This component draws the red circled top OTU number per phylum in a column inside the "Relative Abundance" table.
 **/
export class AbundanceTopOTU {

    @Input()
    topOTUCount: number;

    /**
     * The number of digits to accommodate when sizing the ellipse. Note this
     * may not be equal to the number of digits in `topOTUCount`, e.g., if
     * a bunch of these will be displayed in a table and all should be the same
     * size.
     */
    @Input()
    numDigits: number;

    width: number = 36;

    height: number = 20;
    
    /** Returns an appropriate x-radius for the ellipse based on `numDigits`. */
    getRx(): number {
        var returnVal: number;
        if (this.numDigits < 3) {
            returnVal = 8.5;
        } else if (this.numDigits < 4) {
            returnVal = 9.5;
        } else if (this.numDigits < 5) {
            returnVal = 13;
        } else {
            returnVal = 20; // TODO better way of handling these, in case we ever allow so many top features
        }
        return returnVal;
    }
}
