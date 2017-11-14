import {Pipe, PipeTransform} from '@angular/core';
/**
 * Format float numbers based on KnowEng requirement
 */
@Pipe({name: 'numFormatter'})
export class NumberFormatPipe implements PipeTransform {
    /**
     * Formats a float number according to rules in KNOW-147
     * Args:
     *      value: the number to be formatted
     *      keepLeadingZero: there are cases where we need to keep 0 before . and format number like
     *          0.23 to just .23. By default, we will keep the leading 0.
     *      keepDecimalPart: When true, keeps decimal part for numbers < 100;
     *          when false, discards decimal part for numbers < 100. Note that
     *          numbers >= 100 will have no decimal part regardless of this
     *          parameter.
     * Returns:
     *     string: The formatted number according to the rule
     */
    transform(value: number, keepLeadingZero = true, keepDecimalPart = true): string {
        let absVal = Math.abs(value);
        // determine number of digits after the decimal point
        let decimalDigits = 2;
        if (absVal >= 100 || !keepDecimalPart) {
            decimalDigits = 0;
        } else if ( absVal >= 10 && absVal < 100) {
            decimalDigits = 1;
        }
        let returnVal = value.toFixed(decimalDigits);
        // handle leading zero
        if (!keepLeadingZero) {
            returnVal = returnVal.replace(/^0\./, '.');
        }
        return returnVal;
    }
}
