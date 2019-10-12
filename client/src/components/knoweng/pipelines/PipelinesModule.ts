import {NgModule} from '@angular/core';
import {CommonModule} from '@angular/common';
import {FormsModule} from '@angular/forms';

import {TooltipModule, BsDropdownModule } from 'ngx-bootstrap';
// note: for ngx-bootstrap 1.6.6, ModalModule will be included here without forRoot
// and will also be included in KnowengCommonModule with forRoot
// https://github.com/valor-software/ngx-bootstrap/issues/1903
import { ModalModule } from 'ngx-bootstrap';
import { SlimScrollModule } from 'ng2-slimscroll';
import {FileUploadModule} from 'ng2-file-upload';

import {NestCommonModule} from '../../common/NestCommonModule';
import {KnowengCommonModule} from '../common/KnowengCommonModule';
import {PipelinesRoutingModule} from './PipelinesRoutingModule';

import {FilePicker} from './FilePicker';
import {FormContainer} from './FormContainer';
import {FormEntryPanel} from './FormEntryPanel';
import {FormReviewPanel} from './FormReviewPanel';
import {FormSuccessPanel} from './FormSuccessPanel';
import {GroupedMultiSelector} from './GroupedMultiSelector';
import {HelpPanel} from './HelpPanel';
import {PipelineList} from './PipelineList';
import {PipelineSelector} from './PipelineSelector';
import {Pipelines} from './Pipelines';
import {TemplatePanel} from './TemplatePanel';

@NgModule({
    imports: [
        CommonModule, 
        FormsModule, 
        TooltipModule.forRoot(),
        BsDropdownModule.forRoot(), 
        ModalModule, 
        SlimScrollModule, 
        PipelinesRoutingModule, 
        NestCommonModule, 
        KnowengCommonModule, 
        FileUploadModule
    ],
    declarations: [
        FilePicker,
        FormContainer,
        FormEntryPanel,
        FormReviewPanel,
        FormSuccessPanel,
        GroupedMultiSelector,
        HelpPanel,
        PipelineList,
        PipelineSelector,
        Pipelines,
        TemplatePanel
    ],
    exports: []
})

export class PipelinesModule { }
