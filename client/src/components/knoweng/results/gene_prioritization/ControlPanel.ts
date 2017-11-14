import {Component, OnInit, OnChanges, Input, Output, EventEmitter} from '@angular/core';
//import {DecimalPipe} from '@angular/common';

import {Job} from '../../../../models/knoweng/Job';
import {GeneScores, Result} from '../../../../models/knoweng/results/GenePrioritization';

//import {GradientLegend} from './GradientLegend';
//import {ResponseSelector} from './ResponseSelector';
//import {Slider} from './Slider';

@Component({
    moduleId: module.id,
    selector: 'gp-control-panel',
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
    currentNumTopGenes: number;

    @Input()
    selectedResponses: string[];
    
    @Input()
    result: Result;
    
    @Output()
    updatedNumTopGenes: EventEmitter<number> = new EventEmitter<number>();

    @Output()
    updatedSelectedResponses: EventEmitter<string[]> = new EventEmitter<string[]>();
    
    totalGenesSelectedCount: number;

    constructor() {
    }
    ngOnInit() {
       
    }
    ngOnChanges() {
        this.updateTotalGenesSelectedCount();
    }
    updateNumCurrentTopGenes(num: number): void {
        this.currentNumTopGenes = num;
        this.updateTotalGenesSelectedCount();
        this.updatedNumTopGenes.emit(num);
    }
    updateSelectedResponses(responses: string[]): void {
        this.selectedResponses = responses;
        this.updateTotalGenesSelectedCount();
        this.updatedSelectedResponses.emit(responses);
    }
    updateTotalGenesSelectedCount(): void {
        let topGenesSet: d3.Set = d3.set();
        this.selectedResponses.forEach((response: string) => {
            let geneScores: GeneScores = this.result.scores.scoreMap.get(response);
            geneScores.orderedGeneIds.slice(0, this.currentNumTopGenes).forEach((geneId: string) => {
                topGenesSet.add(geneId);
            });
        });
        this.totalGenesSelectedCount = topGenesSet.size();
    }
}
