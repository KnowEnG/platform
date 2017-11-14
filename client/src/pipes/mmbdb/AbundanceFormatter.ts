import {Pipe, PipeTransform} from '@angular/core';
/*
 * Formats a relative abundance percentage for display.
 * Usage:
 *   value | abundanceFormatter:includeSign
*/
@Pipe({name: 'abundanceFormatter'})
export class AbundanceFormatter implements PipeTransform {
    /**
     * Formats a relative abundance percentage.
     * 
     * Args:
     *     input (number): The relative abundance percentage (i.e., the raw
     *         ratio * 100).
     *     includeSign (boolean): Whether to include an initial +/-.
     * 
     * Returns:
     *     string: The formatted relative abundance percentage.
     */
    transform(value: number, includeSign: boolean): string {
        var returnVal: string;
        if (value == 0) {
            returnVal = "0";
        } else {
            if (includeSign) {
                if (value > 0) {
                    returnVal = "+";
                } else {
                    returnVal = "-";
                }
            } else {
                returnVal = "";
            }
            var abs: number = Math.abs(value);
            if (abs < 0.05) {
                returnVal += " <.05";
            } else if (abs < 1) {
                returnVal += abs.toFixed(2);
            } else if (abs < 9) {
                returnVal += abs.toFixed(1);
            } else {
                returnVal += abs.toFixed(0);
            }
        }
        return returnVal;
    }
}
