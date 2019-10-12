import {HeatmapPane} from './HeatmapPane';
import {ColorGradientPicker} from '../common/ColorGradientPicker';
import {Spreadsheet, Row, NumericRow, CategoricRow} from '../../../../models/knoweng/results/SpreadsheetVisualization';

/**
 * Represents a row that may be enabled for display as a single-row heatmap.
 * Differs from the Row class defined in the models file in that an instance of
 * SelectableRowData can exist before the corresponding Row's data has been
 * loaded from the server.
 * Could potentially split its RowSelector responsibilites (values from server
 * not required) and its CellHeatmap responsibilities (values from server
 * required, ready to display with color scale, etc., and sharing many features
 * with primary heatmaps) into two separate classes.
 */
export class SelectableRowData {
    private colorRGBValues: string[] = [];
    private colorScale: d3.scale.Linear<string, string> | d3.scale.Ordinal<string, {}> = null;
    private valueRange: number[] | string[] = [];
    constructor(
        public selected: boolean,
        public spreadsheet: Spreadsheet,
        public rowIdx: number) {
    }
    getSoftHyphenatedName(): string {
        // escape HTML entities
        let returnVal = this.getName().replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
        // in replacement on next line, $& = matched string; &shy; = soft hyphen
        // figuring it's safe to hyphenate on...
        // existing hyphen (but won't include in regex below, because we don't need a soft hypen after a hard hypen)
        // underscore, colon, comma, period, semicolon, slash, tilde
        // lowercase letter followed by uppercase letter
        return returnVal.replace(/[_:,.;\/~]|[a-z](?=[A-Z])/g, "$&&shy;");
    }
    getScore(): number {
        return this.spreadsheet.rowCorrelations[this.rowIdx];
    }
    getName(): string {
        return this.spreadsheet.rowNames[this.rowIdx];
    }
    getType(): string {
        return this.spreadsheet.rowTypes[this.rowIdx];
    }
    getValueRange(): number[] | string[] {
        return this.valueRange;
    }
    /**
     * Note that for numeric rows, returns color scale that accepts values normalized to [0, 1],
     * not raw values. TODO change? Find references, including RolloverLeftNumericInfo constructor
     * in SingleRowHeatmap.ts and calculateLayout() in MiniDistributionGraph.ts.
     */
    getColorScale(): d3.scale.Linear<string, string> | d3.scale.Ordinal<string, {}> {
        return this.colorScale;
    }
    getColorRGBValues(): string[] {
        return this.colorRGBValues;
    }
    /**
     * Returns the Row object for this row if it's in memory, else null.
     */
    getRawRow(): Row {
        let returnVal: Row = null;
        let rowKey = "" + this.rowIdx;
        if (this.spreadsheet.rowIdxToRowMap.has(rowKey)) {
            returnVal = this.spreadsheet.rowIdxToRowMap.get(rowKey);
        }
        return returnVal;
    }
    updateData(): void {
        let rawRow = this.getRawRow();
        if (rawRow !== null) {
            let rowType = this.getType();
            if (rowType == 'numeric') {
                let numericRow = <NumericRow> rawRow;
                let rawValues = <number[]> numericRow.getValuesOrderedBySampleNames();
                this.valueRange = [numericRow.getMin(), numericRow.getMax()];
                let colorScale = (this.valueRange[0] < 0 && this.valueRange[1] > 0)? ColorGradientPicker.DEFAULT_TWO_COLORS_GRADIENT: ColorGradientPicker.DEFAULT_ONE_COLOR_GRADIENT;
                let percentScale = d3.scale.linear().domain(this.valueRange).range([0, 1]);
                this.colorRGBValues = rawValues.map((cell: number) => {
                    let color = HeatmapPane.missingValueColor;
                    if (cell != null) {
                        color = colorScale(percentScale(cell));
                    }
                    return color;
                });
                // note: need to cast this to the particular scale type before
                // calling, else ts will complain
                this.colorScale = colorScale;
            } else if (rowType== 'categoric') {
                let categoricRow = <CategoricRow> rawRow;
                let rawValues = <string[]> categoricRow.getValuesOrderedBySampleNames();
                this.valueRange = categoricRow.getDistinctValues();
                let numberOfCategories = this.valueRange.length;
                let colorRange: string[] = null;
                if (this.valueRange[this.valueRange.length - 1] === null) {
                    colorRange = HeatmapPane.categoricalPalette.slice(0, numberOfCategories - 1);
                    colorRange.push(HeatmapPane.missingValueColor);
                } else {
                    colorRange = HeatmapPane.categoricalPalette.slice(0, numberOfCategories);
                }
                let colorScale = d3.scale.ordinal().domain(this.valueRange).range(colorRange);
                this.colorRGBValues = rawValues.map((cell: string) => {
                    return <string>colorScale(cell);
                });
                // note: need to cast this to the particular scale type before
                // calling, else ts will complain
                this.colorScale = colorScale;
            } else {
                //not yet supported
            }
        } else {
            this.colorRGBValues = [];
            this.colorScale = null;
            this.valueRange = [];
        }
    }
}


/**
 * Represents a spreadsheet that can be togged on/off in the dropdown
 * that controls the primary spreadsheets (multi-row heatmaps). A spreadsheet
 * can be a normal, SSV-style spreadsheet or a consensus matrix for SC. (That's
 * why we're using the fileId here: fileId is available in both cases, can be
 * resovled to the filename we need to display on screen, and can be traced
 * back to the spreadsheet or consensus matrix as needed.)
 */
export class SelectablePrimarySpreadsheet {
    constructor(
        public selected: boolean,
        public fileId: number
    ) { }
}