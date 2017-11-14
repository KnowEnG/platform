import {NgModule} from '@angular/core';
import {CommonModule} from '@angular/common';

import { BsDropdownModule } from 'ngx-bootstrap';

import {NestCommonModule} from '../../../common/NestCommonModule';
import {ResultsCommonModule} from '../common/ResultsCommonModule';

import {DataArea} from './DataArea';
import {HeatmapPane} from './HeatmapPane';
import {StatsPane} from './StatsPane';
import {SCVisualization} from './SCVisualization';

@NgModule({
    imports: [CommonModule, BsDropdownModule.forRoot(), NestCommonModule, ResultsCommonModule],
    declarations: [
        DataArea,
        HeatmapPane,
        StatsPane,
        SCVisualization
    ],
    exports: [SCVisualization]
})

export class SCModule { }