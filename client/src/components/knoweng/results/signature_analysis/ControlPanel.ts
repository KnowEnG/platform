import {Component, OnInit, OnChanges, Input, Output, EventEmitter} from '@angular/core';

import {Job} from '../../../../models/knoweng/Job';
import {SampleScores, Result} from '../../../../models/knoweng/results/SignatureAnalysis';

@Component({
    moduleId: module.id,
    selector: 'sa-control-panel',
    templateUrl: './ControlPanel.html',
    styleUrls: ['./ControlPanel.css']
})

export class ControlPanel implements OnInit, OnChanges {
    class = 'relative';

    @Input()
    job: Job;

    @Input()
    gradientMaxColor: string;

    @Input()
    gradientMinColor: string;

    @Input()
    gradientMaxValue: number;

    @Input()
    gradientMinValue: number;

    @Input()
    currentNumTopSamples: number;

    @Input()
    selectedSignatures: string[];
    
    @Input()
    result: Result;
    
    @Output()
    updatedNumTopSamples: EventEmitter<number> = new EventEmitter<number>();

    @Output()
    updatedSelectedSignatures: EventEmitter<string[]> = new EventEmitter<string[]>();
    
    totalSamplesSelectedCount: number;
    maxNumTopSamples: number;

    constructor() {
    }
    ngOnInit() {
       
    }
    ngOnChanges() {
        this.updateMaxNumTopSamples();
        this.updateTotalSamplesSelectedCount();
    }
    updateMaxNumTopSamples(): void {
        let numSamples = null;
        if (this.result) {
            numSamples = this.result.getNumberOfSamples();
        }
        if (numSamples) {
            this.maxNumTopSamples = numSamples;
        } else {
            this.maxNumTopSamples = 1;
        }
    }
    updateCurrentNumTopSamples(num: number): void {
        this.currentNumTopSamples = num;
        this.updateTotalSamplesSelectedCount();
        this.updatedNumTopSamples.emit(num);
    }
    updateSelectedSignatures(signatures: string[]): void {
        this.selectedSignatures = signatures;
        this.updateTotalSamplesSelectedCount();
        this.updatedSelectedSignatures.emit(signatures);
    }
    updateTotalSamplesSelectedCount(): void {
        let topSamplesSet: d3.Set = d3.set();
        this.selectedSignatures.forEach((signature: string) => {
            let sampleScores: SampleScores = this.result.scores.scoreMap.get(signature);
            sampleScores.orderedSampleIds.slice(0, this.currentNumTopSamples).forEach((sampleId: string) => {
                topSamplesSet.add(sampleId);
            });
        });
        this.totalSamplesSelectedCount = topSamplesSet.size();
    }
}
