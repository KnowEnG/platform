import {Component, Input, Output, EventEmitter} from '@angular/core';

import {FileService} from '../../../services/knoweng/FileService';
import {FileUploadService} from '../../../services/knoweng/FileUploadService';

@Component({
    moduleId: module.id,
    selector: 'gene-paste-modal',
    templateUrl: './GenePasteModal.html',
    styleUrls: ['./GenePasteModal.css']
})

export class GenePasteModal {
    class = 'relative';
    
    @Input()
    defaultProjectId: number;
    
    @Input()
    userName: string;
    
    @Output()
    close: EventEmitter<boolean> = new EventEmitter<boolean>();
    
    suggestedFileName: string = "MyGeneList";

    geneFileModel: GeneFile;
    
    fileNameChanged: boolean = false;
    
    constructor(private _fileService: FileService, private _fileUploadService: FileUploadService) {
        let today: Date = new Date();
        this.suggestedFileName +=  "_" + today.getFullYear() + (today.getMonth()+1) + today.getDate() 
            + "_" + today.getHours() + today.getMinutes() + today.getSeconds() + ".txt";
        this.geneFileModel = new GeneFile("", this.suggestedFileName);
    }
    
    onDone() {
        let formattedList = this.geneFileModel.geneList.replace(/[ \n\s]+/g, "\n");
        let fullContents = ['Pasted Gene List\n'];
        fullContents.push(formattedList)
        this._fileUploadService.saveFileFromLiteral(this.geneFileModel.fileName, fullContents);
        this.close.emit(true);
    }
    
    onCancel() {
        this.close.emit(true);
    }
    
    onMouseEnter(event: Event) {
        this.fileNameChanged = true;
    }
    
}

export class GeneFile {
    constructor(
        public geneList: string,
        public fileName: string
    ) { }
}

