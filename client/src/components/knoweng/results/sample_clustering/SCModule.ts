import {NgModule} from '@angular/core';
import {CommonModule} from '@angular/common';
import {FormsModule} from '@angular/forms';
import {AngularDraggableModule} from 'angular2-draggable';
import {BsDropdownModule, TooltipModule, PopoverModule, TypeaheadModule} from 'ngx-bootstrap';

import {NestCommonModule} from '../../../common/NestCommonModule';
import {ResultsCommonModule} from '../common/ResultsCommonModule';
import {SSModule} from '../spreadsheet_visualization/SSModule';

import {NumberFormatPipe} from '../../../../pipes/knoweng/NumberFormatPipe';

import {ConsensusVisualization} from './ConsensusVisualization';
import {DataArea} from './DataArea';
import {SCVisualization} from './SCVisualization';

@NgModule({
    imports: [
        CommonModule,
        FormsModule,
        BsDropdownModule.forRoot(),
        TypeaheadModule.forRoot(),
        AngularDraggableModule,
        NestCommonModule,
        ResultsCommonModule,
        SSModule,
        PopoverModule,
        TooltipModule
    ],
    declarations: [
        DataArea,
        ConsensusVisualization,
        SCVisualization
    ],
    exports: [
        SCVisualization
    ]
})

export class SCModule { }