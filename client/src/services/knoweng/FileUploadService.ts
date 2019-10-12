import {Injectable, NgZone} from '@angular/core';
import {FileUploader, FileItem} from 'ng2-file-upload';
import {Http, RequestMethod, Headers, Response, ResponseContentType} from '@angular/http';
import {AuthHttp} from 'angular2-jwt';

import {FileService} from './FileService';
import {ProjectService} from './ProjectService';
import {SessionService} from '../common/SessionService';
import {LogService} from '../common/LogService';

import {Project} from '../../models/knoweng/Project';

@Injectable()
export class FileUploadService {
    private uploader: FileUploader = null;
    private uploaderQueue: FileItem[] = [];
    private permitCancel: boolean = false; 
    private defaultProject: Project;
    private userName: string;
    
    constructor(private authHttp: AuthHttp,
                private http: Http,
                private logger: LogService, 
                private sessionService: SessionService,
                private fileService: FileService,
                private projectService: ProjectService,
                private zone: NgZone) {
            let token = sessionService.getToken();
            this.uploader = new FileUploader({
                url: '/api/v2/files',
                autoUpload: true,
                authToken: 'Bearer ' + token
            });
            this.uploaderQueue = this.uploader.queue;
            
            // Get the real Default Project id because it is not necessarily with id=1
            // TODO: Revisit this solution while doing KNOW-410
            // See https://opensource.ncsa.illinois.edu/jira/browse/KNOW-410
            projectService.getDefaultProjectAsync().subscribe(defaultProject => {
                if (defaultProject) {
                    this.userName = sessionService.getDisplayName();
                    this.defaultProject = defaultProject;
                    
                    this.uploader.onBuildItemForm = (item, form) => {
                        form.append('project_id', this.defaultProject._id);
                    };
                }
            });
           
            this.uploader.onProgressItem = (fileitem, progress) => {
                this.zone.run(() => {
                    fileitem.progress = progress;
                });
            };
            this.uploader.onCompleteItem  = (item, response, status, headers) => {
                fileService.triggerFetch();
            };
            this.uploader.onSuccessItem = (item, response, status, headers) => {
                this.uploader.removeFromQueue(item);
            };
            this.uploader.onCancelItem = (item, response, status, headers) => {
                if(!this.permitCancel)
                    this.uploader.uploadItem(item);
            };
    }
    
    getUploader(): FileUploader {
        return this.uploader;
    }
    
    getUploaderQueue(): FileItem[] {
        return this.uploaderQueue;
    }
    
    // Given a String literal, create and save (upload) a new File from it
    saveFileFromLiteral(desiredFilename: string, contents: any) {
        // Build up a new file from the given contents
        let date: number = new Date().getTime();
        let file = new File([contents], desiredFilename, {type: "text/plain", lastModified: date});
        let fileItem = new FileItem(this.uploader, file, { autoUpload: true });
        this.getUploaderQueue().push(fileItem);
        fileItem.upload();
    }
    
    // Given a URL, create and save (upload) a new File from it
    // ** WARNING **
    //   needs attention for Safari--users would get 0-byte files
    // ** WARNING **
    saveFileFromURL(desiredFilename: string, url: string) {
        let observable = this.http.get(url, {
            method: RequestMethod.Get,
            responseType: ResponseContentType.Text,
        });
        
        observable.subscribe((response: any) => {
            this.saveFileFromLiteral(desiredFilename, response["_body"]);
        });
        
        return observable.share();
    }
}