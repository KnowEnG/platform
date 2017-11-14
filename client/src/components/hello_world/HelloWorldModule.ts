import {NgModule} from '@angular/core';
import {BrowserModule} from '@angular/platform-browser';
import {HttpModule} from '@angular/http';
import {FormsModule} from '@angular/forms';
import {HelloWorldRoutingModule} from './HelloWorldRoutingModule';

import {HelloWorldComponent} from './HelloWorldComponent';
import {AdminComponent} from './AdminComponent';
import {DashboardComponent} from './DashboardComponent';
import {SimplestDtoComponent} from "./SimplestDtoComponent";

@NgModule({
    imports: [
        BrowserModule,
        FormsModule, 
        HttpModule,
        HelloWorldRoutingModule
    ],
    declarations: [
        HelloWorldComponent,
        SimplestDtoComponent,
        AdminComponent,
        DashboardComponent
    ],
    bootstrap: [HelloWorldComponent]
})

export class HelloWorldModule {
    
}