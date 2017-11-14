import {Pipe, PipeTransform} from '@angular/core';
/*
 * Truncates strings longer than a maximum length.
 * Usage:
 *   value | truncator:maxLength
 * Load this via NestCommonModule.
*/
@Pipe({name: 'truncator'})
export class Truncator implements PipeTransform {
    /**
     * Truncates strings longer than a maximum length.
     * 
     * Args:
     *     input (string): The string that may need to be truncated.
     *     maxLength (number): The maximum length of the output string. Note
     *         that any string longer than maxLength will be truncated to length
     *         maxLength-1 and an ellipsis will be added at the end, for a total
     *         output length of maxLength. Using the ellisis unicode literal
     *         below instead of the &hellip; HTML entity to keep the template
     *         binging simple; we'd want to escape HTML in the input string but
     *         not escape the &hellip; added here.
     * 
     * Returns:
     *     string: The input string, truncated if necessary.
     */
    transform(input: string, maxLength: number): string {
        var returnVal: string = "";
        if (input !== null) {
            if (input.length <= maxLength) {
                returnVal = input;
            } else {
                returnVal = input.substring(0, maxLength) + "…";
            }
        }
        return returnVal;
    }
}
