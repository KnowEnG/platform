import {NgModule} from '@angular/core';
import {CommonModule} from '@angular/common';

import { SlimScrollModule } from 'ng2-slimscroll';
import {TooltipModule} from 'ngx-bootstrap';

import {NestCommonModule} from '../../common/NestCommonModule';
import {KnowengCommonModule} from '../common/KnowengCommonModule';
import {GPModule} from './gene_prioritization/GPModule';
import {GSCModule} from './gene_set_characterization/GSCModule';
import {SCModule} from './sample_clustering/SCModule';
import {SSModule} from './spreadsheet_visualization/SSModule';
import {ResultsRoutingModule} from './ResultsRoutingModule';

import {ResultPanel} from './ResultPanel';
import {Results} from './Results';
import {ResultsTable} from './ResultsTable';
import {ResultsTableBody} from './ResultsTableBody';
import {ResultsTablePanel} from './ResultsTablePanel';
import {ResultsVisualization} from './ResultsVisualization';

@NgModule({
    imports: [
        CommonModule,
        SlimScrollModule,
        TooltipModule.forRoot(),
        NestCommonModule,
        KnowengCommonModule,
        GPModule,
        GSCModule,
        SCModule,
        SSModule,
        ResultsRoutingModule
    ],
    declarations: [
        ResultPanel,
        Results,
        ResultsTable,
        ResultsTableBody,
        ResultsTablePanel,
        ResultsVisualization
    ],
    exports: []
})

export class ResultsModule { }