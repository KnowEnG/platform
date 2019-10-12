import {Component, Input, OnChanges} from '@angular/core';

import {Result, SampleScores} from '../../../../models/knoweng/results/SignatureAnalysis';

@Component ({
    moduleId: module.id,
    selector: 'signature-plot',
    styleUrls: ['./SignaturePlot.css'],
    templateUrl: './SignaturePlot.html'
})

export class SignaturePlot implements OnChanges {
    class = 'relative';
    
    @Input()
    result: Result;
    
    @Input()
    signature: string;
    
    @Input()
    numTopSamples: number;
    
    signaturePlotWidth = 235;
    
    signaturePlotHeight = 33;
    
    xScale: any = null;
    
    yScale: any = null;
    
    xNumTopSamples: number;
    
    sampleScorePoints: string = "";
    
    ngOnChanges() {
        let sampleScores: SampleScores = this.result.scores.scoreMap.get(this.signature);
        let orderedScores: number[] = sampleScores.scoreMap.values().sort((a: number, b:number) =>{
           return d3.descending(a, b); 
        });
        let genCount = orderedScores.length;
        this.xScale = d3.scale.linear()
                .domain([0, genCount -1])
                .range([0, this.signaturePlotWidth]);
        this.yScale = d3.scale.linear()
                .domain([orderedScores[genCount - 1], orderedScores[0]])
                .range([this.signaturePlotHeight, 0]);
        for (var count = 0; count < genCount; count++) {
            var x = Math.round(this.xScale(count));
            var y = Math.round(this.yScale(orderedScores[count]));
            var point = x + "," + y + (count == genCount - 1 ? "" : " ");
            this.sampleScorePoints += point;
        }
        this.xNumTopSamples = Math.round(this.xScale(this.numTopSamples));
    }
}
