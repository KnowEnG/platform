import {Component, OnInit, Input, Output, EventEmitter} from '@angular/core';
import {Observable} from 'rxjs/Observable';

import {Pipeline} from '../../../models/knoweng/Pipeline';
import {PipelineService} from '../../../services/knoweng/PipelineService';
import {LogService} from '../../../services/common/LogService';

import {NestFile} from '../../../models/knoweng/NestFile';
import {FileService} from '../../../services/knoweng/FileService';

@Component({
    moduleId: module.id,
    selector: 'file-context-menu',
    templateUrl: './FileContextMenu.html',
    styleUrls: ['./FileContextMenu.css']
})

export class FileContextMenu implements OnInit {
    class = 'relative';
    
    @Input()
    file: NestFile = null;
    
    @Output()
    closeMe: EventEmitter<boolean> = new EventEmitter<boolean> ();
    
    @Output()
    selectedFileUpdated: EventEmitter<NestFile> = new EventEmitter<NestFile>();
    
    pipelines: Pipeline[] = [];
    showSubmenu: boolean = false;
    submenuLeft: number = 0;
    submenuTop: number = 0;
    downloadStatus: string = '';

    constructor(public pipelineService: PipelineService,
                private fileService: FileService,
                private logger: LogService) {
        this.pipelines = this.pipelineService.getPipelines();
    }
    ngOnInit() {
    }
    openSubmenu(event: Event, submenuName: string) {
        var itemBbox: any = (<any>event.target).getBoundingClientRect();

        // default left edge of submenu: 10px left of the main menu's right edge (matches comp)
        // TODO flip to other side of main menu if we're out of room on the right;
        // that's probably uncommon because there's a whole panel to the right of us
        // we'd probably want to flip the carets to the other side of the main menu, etc., too
        this.submenuLeft = itemBbox.right - 10;

        // default top edge of submenu: 4px below the top of the current .item (matches comp)
        this.submenuTop = itemBbox.top + 4;

        // do we need to open the submenu upward instead of downward?
        // estimate the submenu's height
        var parentNode: any = (<any>event.target).parentNode;
        var submenuHeight: number =
            itemBbox.height * this.pipelines.length + // one .item per array element
            parseInt(window.getComputedStyle(parentNode, null).getPropertyValue('padding-top').replace('px', ''), 10) + // .menu's padding-top
            parseInt(window.getComputedStyle(parentNode, null).getPropertyValue('padding-bottom').replace('px', ''), 10); // .menu's padding-bottom
        if (this.submenuTop + submenuHeight > window.innerHeight) {
            // open upward: position the BOTTOM of the submenu 4px below the bottom of the current .item
            var submenuBottom: number = itemBbox.bottom + 4;
            this.submenuTop = submenuBottom - submenuHeight;
        }

        this.showSubmenu = true;
    }
    closeSubmenu() {
        if (this.downloadStatus !== 'start')
            this.showSubmenu = false;
    }
    deleteFile(): void {
        this.fileService.deleteFile(this.file).subscribe(response => {
            // If the deleted file is still selected, de-select it
            if (this.file && this.file._id === response['deleted_id']) {
                this.selectedFileUpdated.emit(this.file = null);
            }
            this.closeMe.emit(true);
        });
    }
    downloadFile(): void {
        var observable: Observable<string> = this.fileService.downloadFile(this.file);
        observable.subscribe ({
            next: status => { 
                this.downloadStatus = status; 
                this.closeMe.emit(false);
            },
            error: err => { 
                this.downloadStatus = "error";
                this.logger.error(err.message, err.stack);
                this.closeMe.emit(true);
            },
            complete: () => { 
                this.downloadStatus = "complete"; 
                this.closeMe.emit(true);
            }
        });
        
    }
    updateFavorite(): void {
        let favorite = this.file.favorite;
        if (favorite == null || favorite == false) {
            this.fileService.updateFileFavorite(this.file, true)
            .subscribe(file => {
                this.file = file;
                this.selectedFileUpdated.emit(this.file);
                this.closeMe.emit(true);
            });
        } else {
             this.fileService.updateFileFavorite(this.file, false)
            .subscribe(file => {
                this.file = file;
                this.selectedFileUpdated.emit(this.file);
                this.closeMe.emit(true);
            });
        } 
    }
}
