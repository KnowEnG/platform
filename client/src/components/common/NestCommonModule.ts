import {NgModule} from '@angular/core';
import {CommonModule, Location} from '@angular/common';
import {FormsModule} from '@angular/forms';

import {TooltipModule} from 'ngx-bootstrap';

import {Login} from './Login';
import {Logout} from './Logout';
import {Tab, Tabset} from './Tabset';
import {ThresholdPicker} from './ThresholdPicker';
import {Truncator} from '../../pipes/common/Truncator';
import {Trunctip} from './Trunctip';
import {ServerStatusService} from '../../services/common/ServerStatusService';
import {SlimScrollSettings} from '../../services/common/SlimScrollSettings';

import {GoogleAnalyticsService} from '../../services/common/GoogleAnalyticsService';
import {LogService} from '../../services/common/LogService';
import {NestErrorHandler} from '../../services/common/NestErrorHandler';
import {PerfMonService} from '../../services/common/PerfMonService';

@NgModule({
    imports: [CommonModule, FormsModule, TooltipModule.forRoot()],
    declarations: [Login, Logout, Tab, Tabset, ThresholdPicker, Truncator, Trunctip],
    providers: [GoogleAnalyticsService, ServerStatusService, LogService, NestErrorHandler, PerfMonService, SlimScrollSettings, Truncator, Location],
    exports: [Tab, Tabset, ThresholdPicker, Truncator, Trunctip]
})

export class NestCommonModule { }
