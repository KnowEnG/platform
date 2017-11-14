import {NgModule} from '@angular/core';
import {CommonModule} from '@angular/common';

import { BsDropdownModule } from 'ngx-bootstrap';

import {NestCommonModule} from '../../../common/NestCommonModule';
import {ResultsCommonModule} from '../common/ResultsCommonModule';

import {SSVisualization} from './SSVisualization';

@NgModule({
    imports: [CommonModule, BsDropdownModule.forRoot(), NestCommonModule, ResultsCommonModule],
    declarations: [
        SSVisualization
    ],
    exports: [SSVisualization]
})

export class SSModule { }