import {NgModule} from '@angular/core';
import {CommonModule} from '@angular/common';

import {KnowengCommonModule} from '../common/KnowengCommonModule';
import {NetworkRoutingModule} from './NetworkRoutingModule';

import {Network} from './Network';

@NgModule({
    imports: [CommonModule, NetworkRoutingModule, KnowengCommonModule],
    declarations: [Network],
    exports: []
})

export class NetworkModule { }