import {Component, OnInit, EventEmitter, Output} from '@angular/core';

import {NestFile} from '../../../models/knoweng/NestFile';

@Component({
    moduleId: module.id,
    selector: 'files-table-panel',
    templateUrl: './FilesTablePanel.html',
    styleUrls: ['./FilesTablePanel.css']
})

export class FilesTablePanel implements OnInit {
    class = 'relative';

    @Output()
    fileSelected: EventEmitter<NestFile> = new EventEmitter<NestFile>();

    constructor() {
    }
    ngOnInit() {
    }
}
