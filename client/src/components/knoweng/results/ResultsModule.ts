import {NgModule} from '@angular/core';
import {CommonModule} from '@angular/common';
import {FormsModule }   from '@angular/forms';

import {SlimScrollModule } from 'ng2-slimscroll';
import {TooltipModule, PopoverModule, ModalModule, BsDropdownModule} from 'ngx-bootstrap';
import {FileUploadModule} from 'ng2-file-upload';

import {NestCommonModule} from '../../common/NestCommonModule';
import {KnowengCommonModule} from '../common/KnowengCommonModule';
import {FPModule} from './feature_prioritization/FPModule';
import {GSCModule} from './gene_set_characterization/GSCModule';
import {SCModule} from './sample_clustering/SCModule';
import {SAModule} from './signature_analysis/SAModule';
import {SSModule} from './spreadsheet_visualization/SSModule';
import {ResultsRoutingModule} from './ResultsRoutingModule';

import {ResultPanel} from './ResultPanel';
import {FilePanel} from './FilePanel';
import {Results} from './Results';
import {ResultsTable} from './ResultsTable';
import {ResultsTableBody} from './ResultsTableBody';
import {ResultsTablePanel} from './ResultsTablePanel';
import {ResultsVisualization} from './ResultsVisualization';

@NgModule({
    imports: [
        CommonModule,
        FormsModule,
        SlimScrollModule,
        TooltipModule.forRoot(),
        PopoverModule.forRoot(),
        BsDropdownModule.forRoot(),
        NestCommonModule,
        KnowengCommonModule,
        FPModule,
        GSCModule,
        SCModule,
        SAModule,
        SSModule,
        ResultsRoutingModule,
        ModalModule,
        FileUploadModule
    ],
    declarations: [
        ResultPanel,
        FilePanel,
        Results,
        ResultsTable,
        ResultsTableBody,
        ResultsTablePanel,
        ResultsVisualization
    ],
    exports: [PopoverModule]
})

export class ResultsModule { }
