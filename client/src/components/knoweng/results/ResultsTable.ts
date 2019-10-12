import {Component, OnInit, OnDestroy, EventEmitter, Output, ViewChild} from '@angular/core';
import {Router} from '@angular/router';
import {Headers, RequestOptions} from '@angular/http';
import {FileUploader, FileItem} from 'ng2-file-upload';
import {Observable} from 'rxjs/Observable';
import {Subscription} from 'rxjs/Subscription';
import {ModalDirective} from 'ngx-bootstrap';

import {FileService} from '../../../services/knoweng/FileService';
import {JobService} from '../../../services/knoweng/JobService';
import {ProjectService} from '../../../services/knoweng/ProjectService';
import {FileUploadService} from '../../../services/knoweng/FileUploadService';
import {ServerStatusService} from '../../../services/common/ServerStatusService';
import {NestFile} from '../../../models/knoweng/NestFile'
import {Job} from '../../../models/knoweng/Job';
import {Project} from '../../../models/knoweng/Project';
import {SessionService} from '../../../services/common/SessionService';
import {LogService} from '../../../services/common/LogService';

@Component({
    moduleId: module.id,
    selector: 'results-table',
    templateUrl: './ResultsTable.html',
    styleUrls: ['./ResultsTable.css']
})

export class ResultsTable implements OnInit, OnDestroy {
    class = 'relative';

    @Output()
    jobSelected: EventEmitter<Job> = new EventEmitter<Job>();
    
    @Output()
    fileSelected: EventEmitter<NestFile> = new EventEmitter<NestFile>();
    
    @ViewChild(ModalDirective) modal : ModalDirective;
    
    //for ng2-file-loader
    uploader: FileUploader;
    uploaderQueue: FileItem[] = [];
    url: string = null;
    errorMessage: string = null;
    modeIsSelect: boolean = true;
    
    userName: string = null;
    showGenePasteModal: boolean = false;

    allFileList: NestFile[] = null;
    allRegularFiles: NestFile[] = null;
    regularFiles: NestFile[] = null;
    allJobOutputFiles = new Map<number, NestFile[]>();
    jobOutputFiles = new Map<number, NestFile[]>();
    allJobs: Job[] = null;
    jobs: Job[] = null;
    projects: Project[] = null;
    fileSub: Subscription;
    jobSub: Subscription;
    projectSub: Subscription;
    
    selectedTag: string = 'all';

    constructor(
       private _router: Router,
       private _fileService: FileService,
       private _fileUploadService: FileUploadService,
       private _statusService: ServerStatusService,
       private _jobService: JobService,
       private _projectService: ProjectService,
       private _sessionService: SessionService,
       private _logger: LogService) {
    }
    ngOnInit() {
        this.userName = this._sessionService.getDisplayName();
        this.fileSub = this._fileService.getFiles().subscribe(
            (files: Array<NestFile>) => {
                this.allFileList = files.slice().sort((a: NestFile, b: NestFile) => {
                    return d3.ascending(a.filename.toUpperCase(), b.filename.toUpperCase());
                });
                /*if (this.uploadingDemoFile) {
                     let pendingDemoFiles = this.selectDemoFilesAndReturnPending();
                     if (pendingDemoFiles.length == 0) {
                         this.uploadingDemoFile = false;
                     }
                }*/
                this.allRegularFiles = this.regularFiles = this.allFileList.filter (file => file.job_id == null);
                let outputFiles = this.allFileList.filter(file => file.job_id != null);
                this.jobOutputFiles.clear();
                this.allJobOutputFiles.clear();
                outputFiles.forEach((file) => {
                    if (!this.jobOutputFiles.has(file.job_id)) {
                        this.jobOutputFiles.set(file.job_id, [] as NestFile[]);
                    }
                    this.jobOutputFiles.get(file.job_id).push(file);
                });
                this.allJobOutputFiles = this.jobOutputFiles;
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
            });
        this.jobSub = this._jobService.getJobs()
            .catch((error: any) => Observable.throw(error))
            .subscribe(
                (jobs: Array<Job>) => {
                    // sort jobs by date
                    this.allJobs = this.jobs = jobs.slice().sort((a: Job, b: Job) => {
                        return d3.descending(a.getCreatedDate().getTime(), b.getCreatedDate().getTime());
                    });
                    this.resort();
                },
                (error: any) => {
                    if (error.status == 401) {
                        this._sessionService.redirectToLogin();
                    } else {
                        alert(`Server error. Try again later`);
                        this._logger.error(error.message, error.stack);
                    }
                });
        this.projectSub = this._projectService.getProjects()
            .catch((error: any) => Observable.throw(error))
            .subscribe(
                (projects: Array<Project>) => {
                    // sort projects by name
                    this.projects = projects.slice().sort((a: Project, b: Project) => {
                        return d3.ascending(a.name.toLowerCase(), b.name.toLowerCase());
                    });
                },
                (error: any) => {
                    if (error.status == 401) {
                        this._sessionService.redirectToLogin();
                    } else {
                        alert(`Server error. Try again later`);
                        this._logger.error(error.message, error.stack);
                    }
                });
                
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
    ngOnDestroy() {
        if (this.fileSub) {
            this.fileSub.unsubscribe();
            this.fileSub = null;
        }
        if (this.jobSub) {
            this.jobSub.unsubscribe();
            this.jobSub = null;
        }
        if (this.projectSub) {
            this.projectSub.unsubscribe();
            this.projectSub = null;
        }
    }
    
    selectTag(tagName: string = "") {
        this.selectedTag = tagName;
        this.resort();
    }
    
    /**
     * Help function to filter the displayed data in the table. Three options are provided, all, recent and favorites.
     **/
    resort(): void {
        let tagName = this.selectedTag;
        if (!tagName || tagName === 'all') {
            this.jobs = this.allJobs.slice();
            this.regularFiles = this.allRegularFiles.slice();
            this.jobOutputFiles = this.allJobOutputFiles;
        } else if (tagName === 'recent') {
            // Figure out the Date 1 week ago
            let oneWeekAgo = new Date();
            oneWeekAgo.setDate(oneWeekAgo.getDate() - 7);
            this.jobs = this.allJobs.slice()
                .filter((a: Job) => oneWeekAgo.getTime() < a.getCreatedDate().getTime())
                .sort((a: Job, b: Job) => d3.descending(a.getCreatedDate().getTime(), b.getCreatedDate().getTime()));
            this.regularFiles = this.allRegularFiles.slice()
                .filter((f: NestFile) => oneWeekAgo.getTime() < f.getCreatedDate().getTime())
                .sort((a: NestFile, b: NestFile) => d3.descending(a.getCreatedDate().getTime(), b.getCreatedDate().getTime()));
            this.jobOutputFiles = this.getOutputFileForSelectedJobs(this.jobs);
        } else if (tagName === 'favorites') {
            //include favorite jobs and non-favorite jobs that have favorite output files
            this.jobs = this.getFavoriteJobs();
            this.regularFiles = this.allRegularFiles.slice()
                .filter((f: NestFile) => f.favorite == true)
                .sort((a: NestFile, b: NestFile) => d3.descending(a.getCreatedDate().getTime(), b.getCreatedDate().getTime()));
            this.jobOutputFiles = this.getOutputFileForSelectedJobs(this.jobs);
        }
    }
    
    /**
     * Given a set of jobs, returns a map of job id and associated job output files
     **/
    getOutputFileForSelectedJobs(jobs: Job[]): Map<number, NestFile[]> {
        let jobIds = this.jobs.map((job: Job) => {return job._id;})
        let allJobOutputFiles = this.allJobOutputFiles;
        let jobOutputFiles = jobIds.reduce(function(obj: Map<number, NestFile[]>, jobId: number){
            if (allJobOutputFiles.get(jobId)) 
                obj.set(jobId, allJobOutputFiles.get(jobId));   
            return obj;}, new Map<number, NestFile[]>());
        return jobOutputFiles;
    }
    
    /**
     * Get jobs that are favorite themselves or having favorite output files
     **/ 
    getFavoriteJobs(): Job[] {
        let favoriteJobs = this.allJobs.slice().filter((a: Job) => a.favorite == true)
                .sort((a: Job, b: Job) => d3.descending(a.getCreatedDate().getTime(), b.getCreatedDate().getTime()));;
        let favoriteOutputFiles = this.allFileList.filter (file => (file.job_id != null && file.favorite == true));
        let nonFavoriteJobIdSet = new Set<number>();
        favoriteOutputFiles.forEach((ff: NestFile) => {
            nonFavoriteJobIdSet.add(ff.job_id); 
        });
        let nonFavoriteJobsWithFavoriteOutputFiles = this.allJobs.slice().filter(
            (a: Job) => (nonFavoriteJobIdSet.has(a._id) && a.favorite == false)
        )
        return favoriteJobs.concat(nonFavoriteJobsWithFavoriteOutputFiles)
                .sort((a: Job, b: Job) => d3.descending(a.getCreatedDate().getTime(), b.getCreatedDate().getTime()));
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
    
    isUrlValid(): boolean {
        // TODO: validate
        return this.url !== null && this.url.length > 0;
    }
    
    getDefaultProjectId() {
        return this._projectService.getDefaultProject()._id;
    }
}
