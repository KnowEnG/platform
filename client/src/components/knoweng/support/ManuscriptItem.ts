import {Component, Input, SimpleChange, OnChanges} from '@angular/core';

import {NestFile} from '../../../models/knoweng/NestFile';
import {FileService} from '../../../services/knoweng/FileService';
import {ProjectService} from '../../../services/knoweng/ProjectService';
import {Manuscript} from './ManuscriptSupport';

@Component({
    moduleId: module.id,
    selector: 'manuscript-item',
    templateUrl: './ManuscriptItem.html',
    styleUrls: ['./ManuscriptItem.css', '../common/SupportAndWelcomeText.css']
})

/**
 * This component mainly deals with displaying a selected manuscript and uploading data files for the manuscript. 
*/
export class ManuscriptItem implements OnChanges {
    class = 'relative';
    
    @Input()
    uploadedFiles: NestFile[];
    
    @Input()
    selectedManuscript: Manuscript;
    
    private uploadingDataFiles: boolean = false;
    
    constructor(private _fileService: FileService,
                private _projectService: ProjectService) {
    }
    
    /**
     * When user files changed in the system, we will re-checked if selected manuscript's data files are uploadable.
     */
    ngOnChanges(changes: {[propertyName: string]: SimpleChange}) { 
        for (let propName in changes) {
            if (propName == 'uploadedFiles') {
                if (this.uploadedFiles && this.selectedManuscript) {
                    let pendingDataFiles = this.getPendingDataFiles();
                    if (pendingDataFiles.length == 0) {
                        this.selectedManuscript.dataLoaded = true;
                        this.uploadingDataFiles = false;
                    }
                }
            }
        }
    }
    
    /**
     * Upload data files 
     */
    uploadSelectedManuscriptDataFiles() {
        let pendingDataFiles = this.getPendingDataFiles();
        if (pendingDataFiles.length > 0) {
            this.uploadingDataFiles = true;
            pendingDataFiles.forEach((dataFile) => {
                this._fileService.copyDemoFile(
                    this.selectedManuscript.dataFilesDirectory + dataFile,
                    this._projectService.getDefaultProject()._id)
                ;
            });
        }
    }
    
    /**
     *Find the data file(s) that hasn't been uploaded for currently selected manuscript
     */
    getPendingDataFiles(): string[] {
        let dataFiles = this.selectedManuscript.dataFiles;
        let loadedFileToLoadedFileName = d3.map(this.uploadedFiles, (file) => file.filename);
        let returnVal: string[] = [];
        dataFiles.forEach(dataFile => {
            if (!loadedFileToLoadedFileName.has(dataFile)) {
                returnVal.push(dataFile);
            }
        });
        return returnVal;
    }
}
