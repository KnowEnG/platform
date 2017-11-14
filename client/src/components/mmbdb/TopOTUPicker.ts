import {Component, Input, OnChanges, SimpleChange} from '@angular/core';
import {ThresholdPicker} from '../common/ThresholdPicker';

@Component ({
    moduleId: module.id,
    selector: 'topotu-picker',
    template: `
        <div>
            <p class="title-otu-picker">
                Select top OTUs to highlight
            </p>
            <threshold-picker
                [sortedValues]="sortedOtuImportanceScores"
                [scales]="otuPickerScales"
                [currentScale]="otuPickerScales[1]"
                [bubbleShape]="'ellipse'"
                [totalHeight]="120"
                [totalWidth]="388"
                [marginTop]="18"
                [marginBottom]="29"
                [sliderSpilloverTop]="0"
                [sliderSpilloverBottom]="0">
            </threshold-picker>
        </div>
    `,
    styleUrls: ['./CohortComparisonTool.css']
})

export class TopOTUPicker implements OnChanges {
    class = 'relative';
    
    // TODO:
    // - implement ngOnChanges in ThresholdPicker and eliminate *ngIf in host.
    // - reconsider this thin wrapper + Mayo-styled implementation in common.
    //   could be cleaner and easier, especially if ThresholdPicker is redone
    //   using a template + css.
    // - replace hardcoded otuPickerScales.
    // - figure out way to represent shadow cutoff in plot.
    // - in seed job, switch to VIM score; maybe add % likelihood as tooltip.

    @Input()
    sortedOtuImportanceScores: number[];

    otuPickerScales: number[] = [];
    
    ngOnChanges(changes: {[propertyName: string]: SimpleChange}) {
        if (this.sortedOtuImportanceScores) {
            this.otuPickerScales = [100, 500, 1000, 5000, 10000, this.sortedOtuImportanceScores.length];
        }
    }
}