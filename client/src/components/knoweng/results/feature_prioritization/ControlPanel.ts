import {Component, OnInit, OnChanges, Input, Output, EventEmitter} from '@angular/core';
//import {DecimalPipe} from '@angular/common';

import {Job} from '../../../../models/knoweng/Job';
import {FeatureScores, Result} from '../../../../models/knoweng/results/FeaturePrioritization';

//import {GradientLegend} from './GradientLegend';
//import {ResponseSelector} from './ResponseSelector';
//import {Slider} from './Slider';

@Component({
    moduleId: module.id,
    selector: 'fp-control-panel',
    templateUrl: './ControlPanel.html',
    styleUrls: ['./ControlPanel.css']
    //directives: [GradientLegend, ResponseSelector, Slider],
    //pipes: [DecimalPipe]
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
    currentNumTopFeatures: number;

    @Input()
    selectedResponses: string[];
    
    @Input()
    result: Result;
    
    @Output()
    updatedNumTopFeatures: EventEmitter<number> = new EventEmitter<number>();

    @Output()
    updatedSelectedResponses: EventEmitter<string[]> = new EventEmitter<string[]>();
    
    totalFeaturesSelectedCount: number;

    constructor() {
    }
    ngOnInit() {
       
    }
    ngOnChanges() {
        this.updateTotalFeaturesSelectedCount();
    }
    updateNumCurrentTopFeatures(num: number): void {
        this.currentNumTopFeatures = num;
        this.updateTotalFeaturesSelectedCount();
        this.updatedNumTopFeatures.emit(num);
    }
    updateSelectedResponses(responses: string[]): void {
        this.selectedResponses = responses;
        this.updateTotalFeaturesSelectedCount();
        this.updatedSelectedResponses.emit(responses);
    }
    updateTotalFeaturesSelectedCount(): void {
        let topFeaturesSet: d3.Set = d3.set();
        this.selectedResponses.forEach((response: string) => {
            let featureScores: FeatureScores = this.result.scores.scoreMap.get(response);
            featureScores.orderedFeatureIds.slice(0, this.currentNumTopFeatures).forEach((featureId: string) => {
                topFeaturesSet.add(featureId);
            });
        });
        this.totalFeaturesSelectedCount = topFeaturesSet.size();
    }
}
