import {Component, OnInit, OnChanges, SimpleChange, Input, EventEmitter, Output} from '@angular/core';
import {FileItem} from 'ng2-file-upload';
import {ISlimScrollOptions} from 'ng2-slimscroll';

import {NestFile} from '../../../models/knoweng/NestFile';
import {Project} from '../../../models/knoweng/Project';
import {ProjectService} from '../../../services/knoweng/ProjectService';
import {SlimScrollSettings} from '../../../services/common/SlimScrollSettings';

@Component({
    moduleId: module.id,
    selector: 'files-table-body',
    templateUrl: './FilesTableBody.html',
    styleUrls: ['./FilesTableBody.css']
})

export class FilesTableBody implements OnInit, OnChanges{
    class = 'relative';

    @Input()
    fileList: NestFile[];
    
    @Input()
    uploaderQueue: FileItem[];
    
    @Input()
    projectList: Project[];

    @Output()
    fileSelected: EventEmitter<NestFile> = new EventEmitter<NestFile>();

    slimScrollOpts: ISlimScrollOptions;

    showContextMenu: boolean = false;
    contextMenuBottom: number = null;
    contextMenuRight: number = null;
    contextMenuFile: NestFile;

    selectedRowIndex: number = null;
    selectedType: string = null; // 'upload' or 'file'
    hasDownloadInProgress: boolean = false;

    constructor(private _projectService: ProjectService,
                private _scrollSettings: SlimScrollSettings) {
    }
    
    ngOnInit() {
        // check ISlimScrollOptions for all options
        this.slimScrollOpts = this._scrollSettings.get();
    }
    
    ngOnChanges(changes: {[propertyName: string]: SimpleChange}) {
        // fileList[] may change if a file was deleted; if so, make sure we
        // update our selected file
        if (changes['selectedRowIndex'] && this.selectedType == 'file' && this.selectedRowIndex !== null) {
            if (this.fileList !== null && this.fileList.length > 0) {
                if (this.selectedRowIndex >= this.fileList.length) {
                    this.selectedRowIndex = this.fileList.length-1;
                }
                this.fileSelected.emit(this.contextMenuFile = this.fileList[this.selectedRowIndex]);
            } else {
                this.fileSelected.emit(null);
            }
        }
    }
    
    selectRow(type: string, index: number) {
        this.selectedType = type;
        this.selectedRowIndex = index;
        if (type == 'file') {
            this.fileSelected.emit(this.contextMenuFile = this.fileList[index]);
        } else {
            this.fileSelected.emit(null);
        }
    }
    isSelected(type: string, index: number) {
        return this.selectedType == type && this.selectedRowIndex == index;
    }
    openContextMenu(event: Event, type: string, index: number) {
        if (!this.hasDownloadInProgress) {
            this.showContextMenu = true;
            this.contextMenuBottom = window.innerHeight - (<any>event).clientY - 85; // 85 looks good on the screen; no science to it
            if (this.contextMenuBottom < 0) {
                this.contextMenuBottom = 0;
            }
            this.contextMenuRight = window.innerWidth - (<any>event).clientX - 15; // 15px is the padding on .context-menu-container
            this.selectedRowIndex = index;
        }
    }
    closeContextMenu(close: boolean) {
        if (close) {
            this.showContextMenu = false;
            this.selectedRowIndex = null;
            this.hasDownloadInProgress = false;
        } else {
            this.hasDownloadInProgress = true;
        }
    }
    closePopup() {
        if (!this.hasDownloadInProgress) {
            this.showContextMenu = false;
            this.selectedRowIndex = null;
        }
    }
    getDateForFile(file: NestFile): Date {
        return new Date(file._created);
    }
}
