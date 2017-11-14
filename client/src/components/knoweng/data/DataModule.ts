import {NgModule} from '@angular/core';
import {CommonModule} from '@angular/common';

import {SlimScrollModule} from 'ng2-slimscroll';
import { BsDropdownModule } from 'ngx-bootstrap';
// note: for ngx-bootstrap 1.6.6, ModalModule will be included here without forRoot
// and will also be included in KnowengCommonModule with forRoot
// https://github.com/valor-software/ngx-bootstrap/issues/1903
import { ModalModule } from 'ngx-bootstrap';
import {FileUploadModule} from 'ng2-file-upload';

import {NestCommonModule} from '../../common/NestCommonModule';
import {KnowengCommonModule} from '../common/KnowengCommonModule';
import {DataRoutingModule} from './DataRoutingModule';

import {Data} from './Data';
import {FileContextMenu} from './FileContextMenu';
import {FilePanel} from './FilePanel';
import {FilesTable} from './FilesTable';
import {FilesTableBody} from './FilesTableBody';
import {FilesTablePanel} from './FilesTablePanel';

@NgModule({
    imports: [CommonModule, BsDropdownModule.forRoot(), ModalModule, SlimScrollModule, DataRoutingModule, NestCommonModule, KnowengCommonModule, FileUploadModule],
    declarations: [Data, FileContextMenu, FilePanel, FilesTable, FilesTableBody, FilesTablePanel],
    exports: []
})

export class DataModule { }