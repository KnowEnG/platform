import {Component, OnChanges, SimpleChange, Input, OnInit, ElementRef, ViewChild, AfterViewChecked} from '@angular/core';
import {Observable} from 'rxjs/Observable';

import {NestFile} from '../../../models/knoweng/NestFile';
import {ProjectService} from '../../../services/knoweng/ProjectService';
import {FileService} from '../../../services/knoweng/FileService';
import {LogService} from '../../../services/common/LogService';

@Component({
    moduleId: module.id,
    selector: 'file-panel',
    templateUrl: './FilePanel.html',
    styleUrls: ['./FilePanel.css']
})

export class FilePanel implements OnChanges, AfterViewChecked{
    class = 'relative';
    
    @Input()
    file: NestFile = null;

    isEditable: boolean = false;
    newFileName: string;
    modal: string = null;
    modalBottom: number = 0;
    modalRight: number = 0;
    downloadStatus: string = '';
    
    projectName: string = "";
    
    @ViewChild('newfilenameinput') newfilenameinput: ElementRef;
    
    constructor(private _fileService: FileService,
                private _projectService: ProjectService,
                private _logger: LogService) {
    }
    
    ngOnChanges(changes: {[propertyName: string]: SimpleChange}) {
        let newlySelectedFile = changes['file'];
        if (newlySelectedFile && newlySelectedFile.currentValue) {
            let projectId = newlySelectedFile.currentValue.project_id;
            let project = this._projectService.getProject(projectId);
            if (project) {
                this.projectName = project.name;
            }
            this.newFileName = newlySelectedFile.currentValue.filename;
        }
    }
    
    /**
     * After the file/job renaming input text field is created, highlight the characters before the last occurance of .
     * (assuming anything after . is the file extension); if there is no ., the whole text is highlighted. 
     */
    ngAfterViewChecked() {
        if(this.newfilenameinput) {
            let input = this.newfilenameinput.nativeElement;
            input.focus();
            let inputText = input.value;
            if (inputText == this.file.filename) {
                let fileTypePos = inputText.lastIndexOf(".");
                fileTypePos = fileTypePos != -1 ? fileTypePos : inputText.length;
                if(input.setSelectionRange) {
                    input.setSelectionRange(0, fileTypePos);
                } else if (input.createTextRange) {
                    var range = input.createTextRange();
                    range.collapse(true);
                    range.moveEnd('character', fileTypePos);
                    range.moveStart('character', 0);
                    range.select();
                }
            }
        } 
    }
    
    deleteFile(): void {
        this._fileService.deleteFile(this.file).subscribe(response => {
            // If the deleted file is still selected, de-select it
            if (this.file && this.file._id === response['deleted_id']) {
                this.file = null;
            }
        });
    }
    downloadFile(): void {
        var observable: Observable<string> = this._fileService.downloadFile(this.file);
        observable.subscribe ({
            next: status => { 
                this.downloadStatus = status; 
            },
            error: err => { 
                this.downloadStatus = "error";
                this._logger.error(err.message, err.stack);
            },
            complete: () => { 
                this.downloadStatus = "complete"; 
            }
        });
    }
    openModal(event: Event, modal: string) {
        this.modal = modal;
        this.modalBottom = window.innerHeight - (<any>event).clientY - 85; // 85 looks good on the screen; no science to it
        if (this.modalBottom < 0) {
            this.modalBottom = 0;
        }
        this.modalRight = window.innerWidth - (<any>event).clientX - 15; // 15 looks good on the screen; no science to it
    }
    closeModal() {
        this.modal = null;
    }
    saveCloseNotesModal(notes: string) {
        this._fileService.updateFileNotes(this.file, notes)
            .subscribe(file => {
                this.file = file;
            });
        this.modal = null;
    }
    getDateForFile(file: NestFile): Date {
        return new Date(file._created);
    }
    
    updateFavorite(): void {
        let favorite = this.file.favorite;
        if (favorite == null || favorite == false) {
            this._fileService.updateFileFavorite(this.file, true)
            .subscribe(file => {
                this.file = file;
            });
        } else {
             this._fileService.updateFileFavorite(this.file, false)
            .subscribe(file => {
                this.file = file;
            });
        } 
    }
    
    /**
     * Rename a name. If new name string is accidently left empty, then file is not renamed, e.g, the original name is kept. 
     */
    updateFileName(): void {
        if(this.newFileName && this.newFileName.length > 0) {
            if (this.newFileName != this.file.filename) {
                this._fileService.updateFileName(this.file, this.newFileName)
                    .subscribe(file => {
                        this.file = file;
                })
            }  
        } else {
            this.newFileName = this.file.filename;
        }
        this.isEditable = false;
    }
}
