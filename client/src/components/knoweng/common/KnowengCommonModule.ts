import {NgModule} from '@angular/core';
import {CommonModule} from '@angular/common';
import {FormsModule} from '@angular/forms';

// note: for ngx-bootstrap 1.6.6, ModalModule will be included here using forRoot
// and will also be included in lazy-loaded modules without forRoot
// https://github.com/valor-software/ngx-bootstrap/issues/1903
import {ModalModule} from 'ngx-bootstrap';
import {AngularDraggableModule} from 'angular2-draggable';

import {Footer} from './Footer';
import {TagEditorModal} from './TagEditorModal';
import {TextboxEditorModal} from './TextboxEditorModal';
import {GenePasteModal} from './GenePasteModal';
import {NavWarnModal} from './NavWarnModal';
import {ErrorModal} from './ErrorModal';

@NgModule({
    imports: [CommonModule, FormsModule, AngularDraggableModule, ModalModule.forRoot()],
    declarations: [Footer, TagEditorModal, TextboxEditorModal, GenePasteModal, NavWarnModal, ErrorModal],
    exports: [Footer, TagEditorModal, TextboxEditorModal, GenePasteModal, NavWarnModal, ErrorModal]
})

export class KnowengCommonModule { }
