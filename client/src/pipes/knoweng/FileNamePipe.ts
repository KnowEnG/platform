import {Pipe, PipeTransform} from '@angular/core';

import {FileService} from '../../services/knoweng/FileService';
import {NestFile} from '../../models/knoweng/NestFile';

/**
 * Converts a file id to file name
 */
@Pipe({name: 'fileName'})
export class FileNamePipe implements PipeTransform {
    private fileName: string = '';
    private fileId: number = null;
    
    constructor(private _fileService: FileService) {
        
    }
    
    /**
     * Formats a string number according to rules in KNOW-147
     * Args:
     *      value: the id to translate
     * Returns:
     *     string: The name of the file matching that id
     */
    transform(value: string): string {
        // Populate features file name based on file id
        // FIXME: We shouldnt need to explicitly query for these, as they should be included in the form summaries list
        // using parseInt because file ids are saved as strings in the launcher; TODO revisit when modeling nest IDs
        let fid: number = parseInt(value, 10);
        if (fid && fid !== this.fileId) {
            this._fileService.getFileById(fid).subscribe((result: NestFile) => {
                this.fileName = NestFile.getFileNameOrPlaceholder(result);
                this.fileId = fid;
            });
        }
        
        return this.fileName;
    }
}
