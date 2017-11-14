export class NestFile {
    _created: string;
    _id: number;
    filename: string;
    project_id: number;
    filesize: number;
    filetype: string;
    uploadername: string;
    notes: string;
    favorite: boolean;
    
    // Handle the case of a file that has been deleted
    static getFileNameOrPlaceholder(file: NestFile): string {
        if (!file) {
            return 'Not Found';
        }
        return file.filename;
    }

    constructor(created: string, id: number , filename: string, project_id: number, 
        filesize?: number, filetype?: string, uploadername?: string, notes?: string, favorite?: boolean) {
        this._created = created;
        this._id = id;
        this.filename = filename;
        this.project_id = project_id;
        this.filesize = filesize;
        this.filetype = filetype;
        this.uploadername = uploadername;
        this.notes = notes;
        this.favorite = favorite;
    }
    
    getFileIcon(filetype: string): string {
        let icon: string = null;
        switch(filetype) {
            case '.tsv': {
                icon = 'img/knoweng/file-tsv.svg';
                break;
            }
            case '.csv': {
                icon = 'img/knoweng/file-csv.svg';
                break;
            }
            case '.txt': {
                icon = 'img/knoweng/file-txt.svg';
                break;
            }
            case '.zip': {
                icon = 'img/knoweng/file-zip.svg';
                break;
            }
            default: {
                icon = 'img/knoweng/file-unknown.svg';
                break;
            }
        }
        return icon;
    }
    
    getFileNameOrPlaceholder(): string {
        return NestFile.getFileNameOrPlaceholder(this);
    }

    /**
     * Returns a file size in bytes as a string formatted for display.
     */
    static byteSizeToPrettySize(byteSize: number): string {
        // based on the python implementation in files_endpoints.py
        let prefixes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
        let current = byteSize;
        let returnVal: string = null;
        for (let i = 0; i < prefixes.length; i++) {
            if (current < 1024 || i == prefixes.length - 1) {
                returnVal = current.toFixed(1) + ' ' + prefixes[i];
                break;
            }
            current /= 1024.0;
        }
        return returnVal;
    }

    /**
     * Returns the size of this file as a string formatted for display.
     */
    getPrettySize(): string {
        return NestFile.byteSizeToPrettySize(this.filesize);
    }
    
    /**
     * given the object recovered from the JSON attached to an Eve POST
     * response, merge the Eve attributes into this object
     * TODO figure out how we want to handle this across the board and
     * standardize the implementation
    */ 
    /*mergeEveAttributes(evePostResponseJson: any): void {
        this._created = evePostResponseJson._created;
        this._id = evePostResponseJson._id;
    }*/
}
