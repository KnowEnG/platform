import {Component, OnInit, OnDestroy, EventEmitter, Output, ViewChild} from '@angular/core';
import {Router} from '@angular/router';
import {Headers, RequestOptions} from '@angular/http';
import {FileUploader, FileItem} from 'ng2-file-upload';

import {Subscription} from 'rxjs/Subscription';
import {ModalDirective} from 'ngx-bootstrap';

import {NestFile} from '../../../models/knoweng/NestFile';
import {Project} from '../../../models/knoweng/Project';
import {FileService} from '../../../services/knoweng/FileService';
import {ProjectService} from '../../../services/knoweng/ProjectService';
import {FileUploadService} from '../../../services/knoweng/FileUploadService';
import {SessionService} from '../../../services/common/SessionService';
import {ServerStatusService} from '../../../services/common/ServerStatusService';
import {LogService} from '../../../services/common/LogService';

@Component({
    moduleId: module.id,
    selector: 'files-table',
    templateUrl: './FilesTable.html',
    styleUrls: ['./FilesTable.css']
})

// TODO refactor this + pipelines/FilePicker
export class FilesTable implements OnInit, OnDestroy {
    class = 'relative';

    @Output()
    fileSelected: EventEmitter<NestFile> = new EventEmitter<NestFile>();
    
    @ViewChild(ModalDirective) modal : ModalDirective;
    
    //for ng2-file-loader
    uploader: FileUploader;
    uploaderQueue: FileItem[] = [];
    
    modeIsSelect: boolean = true;

    url: string = null;
    
    errorMessage: string = null;

    /** All of the current user's projects. */
    projectList: Project[] = [];

    /** All of the current user's files; shown in select mode. */
    allFileList: NestFile[] = [];

    /* For Gene paste modal */
    userName: string;
    showGenePasteModal: boolean = false;
    
    modalBottom: number = 0;
    modalRight: number = 0;
    
    fileSub: Subscription;
    projectSub: Subscription;

    constructor(
        private _router: Router,
        private _fileService: FileService,
        private _projectService: ProjectService,
        private _sessionService: SessionService,
        private _statusService: ServerStatusService,
        private _logger: LogService,
        private _fileUploadService: FileUploadService){
    }
    
    ngOnInit(): void {
        this.userName = this._sessionService.getDisplayName();
        this.fileSub = this._fileService.getFiles().subscribe(
            (files: Array<NestFile>) => {
                this.allFileList = files.slice().sort((a: NestFile, b: NestFile) => {
                    return d3.ascending(a.filename.toUpperCase(), b.filename.toUpperCase());
                });
            },
            (error: any) => {
                if (error.status == 401) {
                    if (!this._router.isActive(this._router.createUrlTree(['/login']), true)) {
                        this._sessionService.redirectToLogin();
                    }
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
    setModeIsSelect(isSelect: boolean): void {
        this.modeIsSelect = isSelect;
    }
    
    openGenePasteModal(event: Event) {
        this.showGenePasteModal = true;
    }
    
    closeGenePasteModal(event: Event) {
        this.showGenePasteModal = false;
    }
}
