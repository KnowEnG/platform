import {NgModule} from '@angular/core';
import {CommonModule} from '@angular/common';

import {BsDropdownModule} from 'ngx-bootstrap';

import {FileUploadService} from '../../services/knoweng/FileUploadService';
import {AuthorizedUserAppRoutingModule} from './AuthorizedUserAppRoutingModule';
import {AuthorizedUserApp} from './AuthorizedUserApp';

@NgModule({
    imports: [
        CommonModule,
        BsDropdownModule.forRoot(),
        AuthorizedUserAppRoutingModule
    ],
    declarations: [AuthorizedUserApp],
    providers: [FileUploadService]
})

export class AuthorizedUserAppModule {}
