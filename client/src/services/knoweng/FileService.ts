import {Injectable} from '@angular/core';
import {Headers, RequestOptions} from '@angular/http';
import {AuthHttp} from 'angular2-jwt';
import {Observable} from 'rxjs/Observable';
import {BehaviorSubject} from 'rxjs/BehaviorSubject';

import {NestFile} from '../../models/knoweng/NestFile';
import {LogService} from '../common/LogService';
import {SessionService} from '../common/SessionService';

import {DownloadUtilities} from '../common/DownloadUtilities';

//import 'rxjs/add/operator/filter';

@Injectable()
export class FileService {

    private _fileUrl: string = '/api/v2/files';
    private _fileDownloadUrl: string = '/api/v2/file_downloads';
    // a stream of the current NestFile[], initialized to []
    private _filesSubject: BehaviorSubject<NestFile[]> = new BehaviorSubject<NestFile[]>([]);

    constructor(private authHttp: AuthHttp, private logger: LogService, private sessionService: SessionService) {
        // as soon as we have an authentication token, or whenever the token
        // changes, fetch data
        this.sessionService.tokenChanged()
            .subscribe(
                data => this.triggerFetch(),
                err => this.logger.error("FileService failed to refresh token")
            );
    }

    /**
     * Returns a stream of the current NestFile[]
     */
    getFiles(): Observable<NestFile[]> {
        return this._filesSubject.asObservable();
    }

    /**
     * Filters the current stream of NestFile[] by the given id, and return the first match
     *
     * NOTE: This method will return undefined if no results match the filter
     */
    getFileById(fileId: number): Observable<NestFile> {
        return this.getFiles()
                .map(files => {
                    // Short-circuit for the race condition where we request
                    // a file by id before the full list has loaded
                    if (!files || !files.length) {
                        return null;
                    }

                    // Filter existing file list by id
                    let results = files.filter(file => file._id === fileId);
                    if (!results.length || results.length > 1) {
                        this.logger.warn(`WARNING: getFileById found ${results.length} results`);
                        return null;
                    }

                    // Return first match
                    return results[0];
                });
    }

    /**
     * Filters the current value of the stream of NestFile[] by the given id, and returns first result
     *
     * NOTE: This method will return undefined if no results match the filter
     */
    getFileByIdSync(id: number): NestFile {
        let returnVal: NestFile = this._filesSubject.getValue().find((file: NestFile) => file._id === id);
        if (returnVal === undefined) {
            this.logger.warn('WARNING: User requested a nonexistent file id (' + id + ')... returning undefined');
        }
        return returnVal;
    }

    /*
     * Fetches the current files from the server.
     */
    triggerFetch() {
        // fetch the current files from the server
        var requestStream = this.authHttp
            .get(this._fileUrl)
            .catch((error: any) => Observable.throw(error))
            .map(res => {
                let fileData: any[] = res.json()._items;
                return fileData.map((fileDatum: any) => new NestFile(
                    fileDatum._created,
                    fileDatum._id,
                    fileDatum.filename,
                    fileDatum.project_id,
                    // TODO filesize will eventually be an integer (TOOL-398)
                    parseInt(fileDatum.filesize, 10),
                    fileDatum.filetype,
                    fileDatum.uploadername,
                    fileDatum.notes,
                    fileDatum.favorite));
            });
        // add the array from the server to the stream of current files
        requestStream.subscribe(
            fArr => this._filesSubject.next(fArr),
            err => {
                this.logger.error("Failed fetching user files");
            });
    }

    /**
    * Create (save) a file by passing content-type: multipart/form-data required by API
    */
    saveFile(formData: FormData, filename: string, projectId: number): void {
        let headers = new Headers();
        headers.append('Accept', 'application/json');
        let options = new RequestOptions({ headers: headers });
        var requestStream = this.authHttp.post(this._fileUrl, formData, options)
            .catch((error: any) => Observable.throw(error))
            .map(res => {
                let fileDatum: any = res.json();
                return new NestFile(
                    fileDatum._created,
                    fileDatum._id,
                    filename,
                    projectId);
            }).share();
        //need to fetch files so the result table will include the file that was just updated
         requestStream.subscribe(
            file => {
                this.triggerFetch();
            },
            err => {
                this.logger.error("Failed saving file: " + filename);
            });
    }

    /**
     * TODO don't call this yet; it doesn't handle the file payload, and we need
     * to integrate with dropzone or switch to something else; for now, just let
     * dropzone POST the file, and have it call triggerFetch()
     * send a POST requst to api to create a new NestFile
     * filename: the filename
     * projectId: the parent project's _id
     */
    createFile(filename: string, projectId: number): void {
        var headers = new Headers();
        headers.append('Content-Type', 'application/json');
        // post the new file to the server
        var url = this._fileUrl + '?reply=whole';
        var requestStream = this.authHttp
            .post(
                url,
                JSON.stringify({filename: filename, project: projectId}),
                {headers: headers}
            )
            .catch((error: any) => Observable.throw(error))
            .map(res => {
                let fileDatum: any = res.json();
                return new NestFile(
                    fileDatum._created,
                    fileDatum._id,
                    filename,
                    projectId);
            });
        // add the new project to the current NestFile[] and publish the updated
        // NestFile[] to the _filesSubject stream
        requestStream.subscribe(
            file => {
                var currentFiles = this._filesSubject.getValue();
                currentFiles.push(file);
                this._filesSubject.next(currentFiles);
            },
            err => {
                this.logger.error("Failed creating file");
            }
        );
    }

    /**
     * Deletes a file.
     */
    deleteFile(file: NestFile): Observable<any> {
        var headers = new Headers();
        headers.append('Content-Type', 'application/json');
        var requestStream = this.authHttp
            .delete(this._fileUrl + '/' + file._id, {
                headers: headers
            })
        .map(resp => resp.json())
        .catch((error: any) => Observable.throw(error))
        .share();
        
        requestStream.subscribe(
            res => {
                this.triggerFetch();
            },
            err => {
                //If the targeted file is not found (likely has been deleted by previous click), e.g HTTP code 404 NOT FOUND, we will not throw any error.
                if (err.status != 404) {
                    this.logger.error("Failed deleting file");
                }
            }
        );
        
        return requestStream;
    }

    /**
     * Given a file, return the URL to download that file
     */
    getDownloadUrl(file: NestFile): string {
        return this._fileDownloadUrl + '/' + file._id;
    }

    /**
     * Downloads a file.
     */
     downloadFile(file: NestFile): Observable<string> {
        return DownloadUtilities.downloadFile(this.getDownloadUrl(file), this.authHttp);
     }

    /**
     * Update file notes field and return updated file back to client if successful
     */
    updateFileNotes(file: NestFile, newNotes: string): Observable<NestFile> {
        let url = this._fileUrl + '/' + file._id + '?reply=whole';
        let headers = new Headers();
        headers.append('Content-Type', 'application/json');
        var payload = {notes: newNotes};
        var requestStream = this.authHttp
            .patch(
                url,
                JSON.stringify(payload),
                {headers: headers}
            )
          .catch((error: any) => Observable.throw(error))
          .map(res => {
                var replyObj: any = res.json();
                var newFile: NestFile = new NestFile(
                    replyObj._created,
                    replyObj._id,
                    replyObj.filename,
                    replyObj.project_id,
                    // TODO filesize will eventually be an integer (TOOL-398)
                    parseInt(replyObj.filesize, 10),
                    replyObj.filetype,
                    replyObj.uploadername,
                    replyObj.notes,
                    replyObj.favorite);
                return newFile;
            }).share();
        //need to fetch files so the result table will include the file that was just updated
         requestStream.subscribe(
            file => {
                this.triggerFetch();
            },
            err => {
                this.logger.error("Failed to update file notes");
            });
        return requestStream;
    }

    /**
     * Update file favorite field and return updated file back to client if successful
     */
    updateFileFavorite(file: NestFile, newFavorite: boolean): Observable<NestFile> {
        let url = this._fileUrl + '/' + file._id + '?reply=whole';
        let headers = new Headers();
        headers.append('Content-Type', 'application/json');
        var payload = {favorite: newFavorite};
        var requestStream = this.authHttp
            .patch(
                url,
                JSON.stringify(payload),
                {headers: headers}
            )
            .catch((error: any) => Observable.throw(error))
            .map(res => {
                var replyObj: any = res.json();
                var newFile: NestFile = new NestFile(
                    replyObj._created,
                    replyObj._id,
                    replyObj.filename,
                    replyObj.project_id,
                    // TODO filesize will eventually be an integer (TOOL-398)
                    parseInt(replyObj.filesize, 10),
                    replyObj.filetype,
                    replyObj.uploadername,
                    replyObj.notes,
                    replyObj.favorite);
                return newFile;
            }).share();
        //need to fetch files so the result table will include the file that was just updated
         requestStream.subscribe(
            file => {
                this.triggerFetch();
            },
            err => {
                this.logger.error("Failed to update file favorites");
            });
        return requestStream;
    }
}
