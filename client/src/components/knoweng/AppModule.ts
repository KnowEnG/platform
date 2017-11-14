import {NgModule, ErrorHandler} from '@angular/core';
import {BrowserModule} from '@angular/platform-browser';
import {FormsModule} from '@angular/forms';
import {HttpModule} from '@angular/http';
import {CommonModule} from '@angular/common';

import {NestCommonModule} from '../common/NestCommonModule';

import {AppRoutingModule} from './AppRoutingModule';
import {CoreModule} from './CoreModule';
import {App} from './App';
import {LoginFormComponent} from './LoginFormComponent';

import {NestErrorHandler} from '../../services/common/NestErrorHandler';

@NgModule({
    imports: [
        BrowserModule,
        FormsModule,
        HttpModule,
        CommonModule,
        AppRoutingModule,
        NestCommonModule,
        CoreModule
    ],
    declarations: [App, LoginFormComponent],
    providers: [
        {provide: ErrorHandler, useClass: NestErrorHandler},
    ],
    bootstrap: [App]
})

export class AppModule {}
