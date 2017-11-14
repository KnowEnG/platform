import {Component, Input, OnInit, OnDestroy, OnChanges, SimpleChange, ViewChild} from '@angular/core';
import {Http, Headers, Response} from '@angular/http';
import {Router} from '@angular/router';
import {ISlimScrollOptions} from 'ng2-slimscroll';
import {Observable} from 'rxjs/Observable';
import {Subscription} from 'rxjs/Subscription';
import {FileUploader, FileItem} from 'ng2-file-upload';
import {ModalDirective} from 'ngx-bootstrap';

import {FileFormField} from '../../../models/knoweng/Form';
import {NestFile} from '../../../models/knoweng/NestFile';
import {Project} from '../../../models/knoweng/Project';
import {SessionService} from '../../../services/common/SessionService';
import {ServerStatusService} from '../../../services/common/ServerStatusService';
import {FileService} from '../../../services/knoweng/FileService';
import {ProjectService} from '../../../services/knoweng/ProjectService';
import {LogService} from '../../../services/common/LogService';
import {SlimScrollSettings} from '../../../services/common/SlimScrollSettings';
import {FileUploadService} from '../../../services/knoweng/FileUploadService';
import {PipelineService} from '../../../services/knoweng/PipelineService';

import {Pipeline} from '../../../models/knoweng/Pipeline';

@Component ({
    moduleId: module.id,
    selector: 'file-picker',
    styleUrls: ['./FilePicker.css'],
    templateUrl: './FilePicker.html'
})

// TODO refactor this + data/FilesTable
export class FilePicker implements OnInit, OnDestroy, OnChanges {
    class = 'relative';
    
    public slimScrollOpts: ISlimScrollOptions;

    @Input()
    fileFormField: FileFormField;

    // Current launcher page index
    @Input()
    currentIndex: number;
    
    // Current launcher pipeline
    @Input()
    pipeline: Pipeline = null;
    
    @ViewChild(ModalDirective) modal : ModalDirective;
    
    url: string = null;
    uploader: FileUploader;
    errorMessage: string = null;

    userName: string;
    showGenePasteModal: boolean = false;

    selectedId: number = null;

    /** All of the current user's projects. */
    projectList: Project[] = [];

    /** All of the current user's files; shown in select mode. */
    allFileList: NestFile[] = [];

    /** All of the files currently uploading; shown at the top of the table in
        upload mode. */
    uploaderQueue: FileItem[] = [];

    modeIsSelect: boolean = true; 
    fileSub: Subscription;
    projectSub: Subscription;
    showGenePasteArea: boolean = false;
    uploadingDemoFile: boolean = false;
    
    // Our demo file metadata is stored in client/data/demofiles.json
    private demoFilesUrl = '/static/data/demofiles.json';
    private demoFiles: any = {};

    constructor(
        private _router: Router,
        private _http: Http,
        private _fileService: FileService,
        private _projectService: ProjectService,
        private _pipelineService: PipelineService,
        private _sessionService: SessionService,
        private _statusService: ServerStatusService,
        private _logger: LogService,
        private _scrollSettings: SlimScrollSettings,
        private _fileUploadService: FileUploadService) {
    }

    ngOnInit(): void {
        // check ISlimScrollOptions for all options
        this.slimScrollOpts = this._scrollSettings.get();
        this.userName = this._sessionService.getDisplayName();
        this.showGenePasteArea = this.fileFormField.allowGenePaste;
        if (this.fileFormField.currentValue) {
            this.selectedId = Number(this.fileFormField.currentValue);
        }
        
        this.fileSub = this._fileService.getFiles().subscribe(
            (files: Array<NestFile>) => {
                this.allFileList = files.slice().sort((a: NestFile, b: NestFile) => {
                    return d3.ascending(a.filename.toUpperCase(), b.filename.toUpperCase());
                });
            },
            (error: any) => {
                if (error.status == 401) {
                    this._sessionService.redirectToLogin();
                } else {
                    alert(`Server error. Try again later`);
                    this._logger.error(error.message, error.stack);
                }
            }
        );
        this.projectSub = this._projectService.getProjects().subscribe(
            (projects: Array<Project>) => {
                this.projectList = projects.slice().sort((a: Project, b: Project) => {
                    return d3.ascending(a.name.toUpperCase(), b.name.toUpperCase());
                });
            },
            (error: any) => {
                if (error.status == 401) {
                    this._sessionService.redirectToLogin();
                } else {
                    alert(`Server error. Try again later`);
                    this._logger.error(error.message, error.stack);
                }
            }
        );
        this.uploader = this._fileUploadService.getUploader();
        this.uploaderQueue = this._fileUploadService.getUploaderQueue();

        this.uploader.onErrorItem = (item, response, status, headers) => {
            if (status == 413) {
                // see files_endpoints.py for a long comment explaining why
                // this case is handled differently
                let maxSize = NestFile.byteSizeToPrettySize(
                    this._statusService.status.maxUploadSize);
                this.errorMessage = 'Your spreadsheet is larger than ' + maxSize +
                    '. Upload a smaller spreadsheet, or contact us about a ' +
                    'premium account.';
            } else {
                this.errorMessage = response; // the body of the http response
            }
            this.uploader.removeFromQueue(item);
            this.modal.show();
        };
        
        let headers = new Headers();
        headers.append('Content-Type', 'application/json');
        this._http.get(this.demoFilesUrl, {headers: headers})
          .map((res: Response) => res.json())
          .catch((error: any) => Observable.throw(error))
          .subscribe((demoFiles: any) => {
              this.demoFiles = demoFiles;
          });
    }

    /** Handles updates to the inputs. */
    ngOnChanges(changes: {[propertyName: string]: SimpleChange}) {
        // we need to reset when the fileFormField changes
        for (let propName in changes) {
            if (propName == 'fileFormField') {
                this.selectedId = null;
                let toMatch = parseInt(this.fileFormField.currentValue, 10);
                for (let i=0; i < this.allFileList.length; i++) {
                    if (this.allFileList[i]._id === toMatch) {
                        this.selectedId = toMatch;
                        break;
                    }
                }
            }
        }
    }

    ngOnDestroy(): void {
        this.fileSub.unsubscribe();
        this.projectSub.unsubscribe();
    }

    setUrl(url: string): void {
        this.url = url;
    }

    isUrlValid(): boolean {
        // TODO: validate
        return this.url !== null && this.url.length > 0;
    }

    toggleItem(item: NestFile): void {
        if (this.selectedId === item._id) {
            this.selectedId = null;
            this.fileFormField.currentValue = null;
        } else {
            this.selectedId = item._id;
            this.fileFormField.currentValue = item._id.toString();
        }
    }

    getDateForFile(file: NestFile): Date {
        return new Date(file._created);
    }
    
    setModeIsSelect(isSelect: boolean) {
        this.modeIsSelect = isSelect;
    }
    
    openGenePasteModal(event: Event) {
        this.showGenePasteModal = true;
    }
    
    closeGenePasteModal(event: Event) {
        this.showGenePasteModal = false;
    }
    
        // Translate pipeline+step => demo file
    getDemoFile() {
        let step = this.currentIndex === 0 ? "features" : "response"; 
        
        // Retrieve our demo file for this stage of the pipeline
        let pipelineDemoFiles: any = this.demoFiles[this.pipeline.slug];
        let demoFile: any = pipelineDemoFiles[step];
        return demoFile;
    }
    
    isDemoFile(filename: string): boolean {
        if (!this.demoFiles || !this.demoFiles[this.pipeline.slug]) {
            return false;
        }
        
        // In UI, compare filename to known demo filename to display "Demo Files" badge 
        let demoFile: any = this.getDemoFile();
        return filename === demoFile.filename;
    }
    
    useDemoData() {
        let demoFile: any = this.getDemoFile();
        let existingFile = this.allFileList.find(file => file.filename === demoFile.filename);
        
        // If not exists, retrieve and upload demo file to the /files endpoint
        if (!existingFile) {
            this.uploadingDemoFile = true;
            this._fileUploadService.saveFileFromURL(demoFile.filename, demoFile.url).subscribe(() => {
                // Gross hack to handle the asynchronous nature here
                // FIXME: There's definitely a "more RxJS way" to do this...
                let context = this;
                let interval = setInterval(() => {
                    // Once the upload finishes (synchronous), automatically select the file
                    let newFile = this.allFileList.find(file => file.filename === demoFile.filename);
                    if (newFile && newFile["_id"]) {
                        // De-select any selected files, then select our new upload
                        context.selectedId = null;
                        context.toggleItem(newFile);
                        context.uploadingDemoFile = false;
                        
                        // Make sure to clean up our timeout when we're done
                        clearInterval(interval);
                        interval = null;
                    }
                }, 1000);
            });
        } else {
            // De-select anything, then select the existing demo file
            this.selectedId = null;
            this.toggleItem(existingFile);
        }
    }
}
