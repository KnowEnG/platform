import {Component, OnChanges, SimpleChange, Input} from '@angular/core';
import {DomSanitizer, SafeStyle} from '@angular/platform-browser';

import {hexToDec} from '../common/CellHeatmap';
import {Result, Cluster, PhenotypeData} from '../../../../models/knoweng/results/SampleClustering';

import {LogService} from '../../../../services/common/LogService';

@Component({
    moduleId: module.id,
    selector: 'heatmap-pane',
    templateUrl: './HeatmapPane.html',
    styleUrls: ['./HeatmapPane.css']
})

export class HeatmapPane implements OnChanges {
    class = 'relative';

    @Input()
    result: Result;

    heatmapWidth = 420;
    heatmapHeight = 420; // was 484 in comp, but forcing square for now--better for samples x samples case

    rowTypeOptions: string[]; // options from LEGAL_ROW_TYPES dictated by current result
    rowTypeOptionsIndex: number;

    primaryHeatmapData: number[][] = null;
    static categoricalPalette = ['#e15d63', '#00a8c9', '#fbba3d', '#063953', '#76ad98', '#ecd490', '#837ab5', '#abdee5', '#dc7f4f', '#567389'];
    static oneColorGradient = ["#e8f5f8", "#c8e0ee", "#a9cae3", "#88b7da", "#63a3d0", "#33667f", "#2d5366", "#253e4d", "#1d2b35", "#12191f"];
    static twoColorGradient = [
        "#00a8c9", "#15a5c4", "#1fa1c0", "#289dba", "#2d9bb6", "#3397b1",
        "#3793ac", "#3b90a7", "#3e8da3", "#40899f", "#438699", "#458295",
        "#478091", "#497c8b", "#4a7887", "#4b7683", "#4c737f", "#4d6f79",
        "#4e6c75", "#4e6871", "#4f656d", "#4f6268", "#505e64", "#505c60",
        "#50595c", "#505558", "#4f5354", "#4f4f4f", "#55524f", "#5c574f",
        "#635a4f", "#695e4f", "#6f614f", "#75654f", "#7c694e", "#826d4e",
        "#88704e", "#8e744d", "#95784d", "#9b7c4d", "#a2814c", "#a8854b",
        "#ae884b", "#b48d4a", "#bb9149", "#c19549", "#c79948", "#cd9d47",
        "#d4a046", "#dba544", "#e2a943", "#e8ae42", "#eeb240", "#f4b63f",
        "#fbba3d"
    ];
    static oneColorGradientScale = HeatmapPane.convertGradientToScale(HeatmapPane.oneColorGradient);
    static twoColorGradientScale = HeatmapPane.convertGradientToScale(HeatmapPane.twoColorGradient);
    static missingValueColor = '#FFFFFF';
    miniHeatmapData: SelectablePhenotypeData[] = [];
    
    showColorBoxRollover: boolean = false;
    clickedPhenotype: SelectablePhenotypeData = null;
    rolloverLeft: number = null;
    rolloverTop: number = null;

    constructor(private logger: LogService, private sanitizer: DomSanitizer) {
    }
    /**
     * Converts a list of colors into a gradient in which the color-stop points
     * are equally spaced.
     */
    static convertGradientToScale(gradient: string[]) {
        let divisor = gradient.length - 1;
        return d3.scale.linear<string>().domain(gradient.map((val: string, index: number) => index/divisor)).range(gradient);
    }
    ngOnChanges(changes: {[propertyName: string]: SimpleChange}) {
        // note: only one input now, so this is overkill, but this is almost as
        // easy as writing a warning comment...
        for (let propName in changes) {
            if (propName == 'result') {
                if (this.result.samplesHeatmap.length > 0) {
                    this.rowTypeOptions = ['samples', 'genes'];
                } else {
                    this.rowTypeOptions = ['genes'];
                }
                this.rowTypeOptionsIndex = 0;
                this.prepareHeatmapPrimaryHeatmapData();
                this.prepareMiniHeatmapData();
            }
        }
    }
    getRowType(): string {
        return this.rowTypeOptions[this.rowTypeOptionsIndex];
    }
    setRowTypeOptionsIndex(index: number): void {
        this.rowTypeOptionsIndex = index;
        this.prepareHeatmapPrimaryHeatmapData();
    }
    prepareHeatmapPrimaryHeatmapData(): void {
        let rawData: number[][];
        switch (this.getRowType()) {
            case 'samples':
                rawData = this.result.samplesHeatmap;
                break;
            case 'genes':
                rawData = this.result.genesHeatmap;
                break;
            default:
                alert("Unknown row type " + this.getRowType() + ". Contact technical support.");
                this.logger.error("Unknown row type: " + this.getRowType());
        }
        let min = d3.min(rawData, (row: number[]) => d3.min(row));
        let max = d3.max(rawData, (row: number[]) => d3.max(row));
        let gradient = min < 0 ? HeatmapPane.twoColorGradientScale : HeatmapPane.oneColorGradientScale;
        let percentScale = d3.scale.linear().domain([min, max]).range([0, 1]);
        this.primaryHeatmapData =
            rawData.map((row: number[]) => {
                return row.map((cell: number) => {
                    let color = HeatmapPane.missingValueColor;
                    if (cell !== null) {
                        color = gradient(percentScale(cell));
                    }
                    return hexToDec(color);
                });
            });
    }
    prepareMiniHeatmapData() {
        let rawData: PhenotypeData[] = this.result.phenotypes;
        let transformedData: SelectablePhenotypeData[] = [];
        for (var i = 0; i < rawData.length; i++ )
        {
            let phenotype: PhenotypeData = rawData[i];
            let rawValues: any = phenotype.values;
            //transform values numerical phenotype (numberical or categorical)
            // previously checked only the first element of rawValues, but if
            // first element happens to be null, we need more
            if (rawValues.some((val: any) => typeof val == "number")) {
                let extent = d3.extent(rawValues);
                let gradient = extent[0] < 0 ? HeatmapPane.twoColorGradientScale : HeatmapPane.oneColorGradientScale;
                let percentScale = d3.scale.linear().domain(extent).range([0, 1]);
                let translatedValues = rawValues.map((cell: number) => {
                    let color = HeatmapPane.missingValueColor;
                    if (cell !== null) {
                        color = gradient(percentScale(cell));
                    }
                    return hexToDec(color);
                });
                transformedData.push(new SelectablePhenotypeData("number", phenotype.name, phenotype.score, translatedValues, false, extent, gradient));
            } else {
                let uniqueValues = this.findUnique(rawValues).sort((valA: string, valB: string) => {
                    let returnVal = d3.ascending(valA, valB);
                    if (isNaN(returnVal)) {
                        if (valA === null) {
                            returnVal = 1;
                        } else {
                            returnVal = -1;
                        }
                    }
                    return returnVal;
                });
                let numberOfCategories = uniqueValues.length;
                let colorRange = HeatmapPane.categoricalPalette.slice(0, numberOfCategories);
                if (uniqueValues[uniqueValues.length - 1] === null) {
                    colorRange[colorRange.length - 1] = HeatmapPane.missingValueColor;
                }
                let scale = d3.scale.ordinal().domain(uniqueValues).range(colorRange);
                let translatedValues = rawValues.map((cell: string) => {
                    return hexToDec(<string>scale(cell));
                });
                transformedData.push(new SelectablePhenotypeData("category", phenotype.name, phenotype.score, translatedValues, false, uniqueValues, scale));
            }
        }
        //sort by phenotype score
        this.miniHeatmapData = transformedData.sort(function(x, y) {return d3.ascending(x.score, y.score);}); // sort ascending for now--these are currently pvals
    }
    findUnique(values: string[]): string[] {
        var n: any = {};
        var r: string[] = [];
	    for(var i = 0; i < values.length; i++) {
		    if (!n[values[i]]) {
	            n[values[i]] = true; 
			    r.push(values[i]); 
		    }
	   }
	   return r;
    }
    
    getWidthOfColLabel(cluster: Cluster): number {
        // in chrome, fractional widths not handled well; TODO revisit
        return cluster.size / this.result.samples.length * this.heatmapWidth;
    }
    getHeightOfRowLabel(cluster: Cluster): number {
        // in chrome, fractional heights seem to be ok
        return cluster.size / this.result.samples.length * this.heatmapHeight;
    }
    getPaddingTopOfRowLabel(cluster: Cluster): number {
        // half of the height minus the approximate height of the font
        return this.getHeightOfRowLabel(cluster) / 2 - 11;
    }
    getSelectedPhenotypes(): SelectablePhenotypeData[] {
        return this.miniHeatmapData.filter((pheno) => pheno.selected);
    }
    getGradientCssForPhenotype(pheno: SelectablePhenotypeData): SafeStyle {
        let domain = pheno.colorScale.domain() as number[];
        let range = pheno.colorScale.range();
        return this.sanitizer.bypassSecurityTrustStyle("linear-gradient(90deg, " +
            range.map((color: string, index: number) => color + " " + (100*domain[index]) + "%").join(", ") +
            ")");
    }
    onCheckboxChange(phenotype: SelectablePhenotypeData) {
        if (phenotype.selected == false)
            phenotype.selected = true;
        else
            phenotype.selected = false;
    }
    
    onColorBoxClick(phenotype: SelectablePhenotypeData, event: MouseEvent) {
        this.showColorBoxRollover = true;
        this.clickedPhenotype = phenotype;
        this.setRolloverCorners(event);
    }
    
    onClose() {
        this.showColorBoxRollover = false;
        this.clickedPhenotype = null;
    }
    
    setRolloverCorners(event: MouseEvent) {
        this.rolloverTop = event.clientY; 
        this.rolloverLeft = event.clientX; 
    }
}

export class SelectablePhenotypeData {
    constructor(
        public type: string,  //prepare to generate different kinds of color gradient
        public name: string,
        public score: number, //number is easiest for sorting; we can translate to scientific notation via pipe
        public values: number[] | string[],
        public selected: boolean,
        public valueRange: number[] | string[],
        public colorScale: d3.scale.Linear<string, string> | d3.scale.Ordinal<string, {}>) {
    }
    getSoftHyphenatedName(): string {
        // escape HTML entities
        let returnVal = this.name.replace(/&/g, "&amp;")
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
}
