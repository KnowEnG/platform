import {NgModule} from '@angular/core';
import {CommonModule} from '@angular/common';
import {BsDropdownModule} from 'ngx-bootstrap';

import {NestCommonModule} from '../../common/NestCommonModule';
import {KnowengCommonModule} from '../common/KnowengCommonModule';
import {SupportRoutingModule} from './SupportRoutingModule';

import {Support} from './Support';
import {ManuscriptSupport} from './ManuscriptSupport'
import {ManuscriptItem} from './ManuscriptItem'

@NgModule({
    imports: [CommonModule, 
        BsDropdownModule.forRoot(),
        SupportRoutingModule, 
        KnowengCommonModule,
        NestCommonModule],
    declarations: [ManuscriptSupport, ManuscriptItem, Support],
    exports: []
})

export class SupportModule { }