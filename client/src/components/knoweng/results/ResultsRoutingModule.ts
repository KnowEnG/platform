import {NgModule} from '@angular/core';
import {RouterModule} from '@angular/router';

import {Results} from './Results';
import {ResultsVisualization} from './ResultsVisualization';

@NgModule({
    imports: [RouterModule.forChild([
        { 
            path: '', 
            children: [
                { path: ':id', component: ResultsVisualization},
                { path: '', component: Results}
            ]
        }
    ])],
    exports: [RouterModule]
})

export class ResultsRoutingModule {}
