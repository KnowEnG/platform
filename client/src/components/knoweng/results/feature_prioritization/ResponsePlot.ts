import {Component, Input, OnChanges} from '@angular/core';

import {Result, FeatureScores} from '../../../../models/knoweng/results/FeaturePrioritization';

@Component ({
    moduleId: module.id,
    selector: 'response-plot',
    styleUrls: ['./ResponsePlot.css'],
    templateUrl: './ResponsePlot.html'
})

export class ResponsePlot implements OnChanges {
    class = 'relative';
    
    @Input()
    result: Result;
    
    @Input()
    response: string;
    
    @Input()
    numTopFeatures: number;
    
    responsePlotWidth = 235;
    
    responsePlotHeight = 33;
    
    xScale: any = null;
    
    yScale: any = null;
    
    xNumTopFeatures: number;
    
    featureScorePoints: string = "";
    
    ngOnChanges() {
        let featureScores: FeatureScores = this.result.scores.scoreMap.get(this.response);
        let orderedScores: number[] = featureScores.scoreMap.values().sort((a: number, b:number) =>{
           return d3.descending(a, b); 
        });
        let genCount = orderedScores.length;
        this.xScale = d3.scale.linear()
                .domain([0, genCount -1])
                .range([0, this.responsePlotWidth]);
        this.yScale = d3.scale.linear()
                .domain([orderedScores[genCount - 1], orderedScores[0]])
                .range([this.responsePlotHeight, 0]);
        this.featureScorePoints = "";
        for (var count = 0; count < genCount; count++) {
            var x = Math.round(this.xScale(count));
            var y = Math.round(this.yScale(orderedScores[count]));
            var point = x + "," + y + (count == genCount - 1 ? "" : " ");
            this.featureScorePoints += point;
        }
        this.xNumTopFeatures = Math.round(this.xScale(this.numTopFeatures));
    }
}
