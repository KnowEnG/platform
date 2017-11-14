import {Component, Input, Output, EventEmitter} from '@angular/core';

import {FileUploader} from 'ng2-file-upload';

@Component({
    moduleId: module.id,
    selector: 'nav-warn-modal',
    templateUrl: './NavWarnModal.html',
    styleUrls: ['./NavWarnModal.css']
})

export class NavWarnModal {
    
    @Input()
    uploader: FileUploader;
    
    @Output()
    flag: EventEmitter<NavWarnModalFlag> = new EventEmitter<NavWarnModalFlag>();
    
    /**
     * cancel items that have not be finished and close this modal
     */
    onCancelUpload(): void {
        this.uploader.cancelAll();
        this.uploader.clearQueue();
        var navWarnFlag: NavWarnModalFlag = {
            closeModal: true,
            closeUploadTab: true
        };
        this.flag.emit(navWarnFlag);
    }
    
    /**
     * close this modal, but keep uploading the remaining files in uploader's queue 
     * and keep the "Upload New Data" tab open
     */
    onFinishUpload(): void {
        var navWarnFlag: NavWarnModalFlag = {
            closeModal: true,
            closeUploadTab: false
        };
        this.flag.emit(navWarnFlag);
    }
}

export interface NavWarnModalFlag {
    closeModal: boolean;  
    closeUploadTab: boolean;  
}