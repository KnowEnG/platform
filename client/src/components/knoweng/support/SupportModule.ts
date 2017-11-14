import {NgModule} from '@angular/core';
import {CommonModule} from '@angular/common';

import {KnowengCommonModule} from '../common/KnowengCommonModule';
import {SupportRoutingModule} from './SupportRoutingModule';

import {Support} from './Support';

@NgModule({
    imports: [CommonModule, SupportRoutingModule, KnowengCommonModule],
    declarations: [Support],
    exports: []
})

export class SupportModule { }