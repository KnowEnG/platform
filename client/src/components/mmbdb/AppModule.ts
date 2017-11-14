import {NgModule} from '@angular/core';
import {BrowserModule} from '@angular/platform-browser';
import {FormsModule} from '@angular/forms';
import {HttpModule} from '@angular/http';

import {NestCommonModule} from '../common/NestCommonModule';

import {LoginFormComponent} from './LoginFormComponent';
import {Logout} from '../common/Logout';
import {AppRoutingModule} from './AppRoutingModule';
import {AppComponent} from './AppComponent';

@NgModule({
    imports: [
        BrowserModule,
        FormsModule,
        HttpModule,
        AppRoutingModule,
        NestCommonModule
    ],
    declarations: [
        AppComponent,
        LoginFormComponent
    ],
    bootstrap: [AppComponent]
})

export class AppModule {}