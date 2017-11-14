import {Component, ChangeDetectorRef, OnChanges, SimpleChange} from '@angular/core';

import {NestFile} from '../../../models/knoweng/NestFile';

@Component({
    moduleId: module.id,
    selector: 'data',
    templateUrl: './Data.html',
    styleUrls: ['./Data.css']
})

export class Data implements OnChanges {
    class = 'relative';
    
    /**
     * This the file the user has selected from the list of
     * files. Its details will be loaded to a panel on the right.
     */
    selectedFile: NestFile = null;
    constructor(private _changeDetector: ChangeDetectorRef) {
    }
    ngOnChanges(changes: {[propertyName: string]: SimpleChange}) {
    }
    onFileSelected(file: NestFile) {
        this.selectedFile = file;
        this._changeDetector.detectChanges();
    }
}
