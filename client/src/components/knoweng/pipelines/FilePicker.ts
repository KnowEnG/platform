import {Component, Input, OnInit, OnDestroy, OnChanges, SimpleChange, ViewChild, ChangeDetectorRef} from '@angular/core';
import {Http, Headers, Response} from '@angular/http';
import {Router} from '@angular/router';
import {ISlimScrollOptions} from 'ng2-slimscroll';
import {Observable} from 'rxjs/Observable';
import {Subscription} from 'rxjs/Subscription';
import {FileUploader, FileItem} from 'ng2-file-upload';
import {ModalDirective} from 'ngx-bootstrap';

import {FileFormField, FormData} from '../../../models/knoweng/Form';
import {Job} from '../../../models/knoweng/Job';
import {NestFile} from '../../../models/knoweng/NestFile';
import {Project} from '../../../models/knoweng/Project';
import {SessionService} from '../../../services/common/SessionService';
import {ServerStatusService} from '../../../services/common/ServerStatusService';
import {JobService} from '../../../services/knoweng/JobService';
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

    // Current launcher pipeline
    @Input()
    pipeline: Pipeline = null;

    @Input()
    formData: FormData = null;
    
    @ViewChild(ModalDirective) modal : ModalDirective;

    url: string = null;
    uploader: FileUploader;
    errorMessage: string = null;

    userName: string;
    showGenePasteModal: boolean = false;

    selectedIds: string[] = [];

    /** All of the current user's projects. */
    projectList: Project[] = [];

    /** All of the current user's files; shown in select mode. */
    allFileList: NestFile[] = [];
    //files that are not produced by running a job
    allRegularFiles: NestFile[] = [];
    regularFiles: NestFile[] = [];

    /** All of the files currently uploading; shown at the top of the table in
        upload mode. */
    uploaderQueue: FileItem[] = [];

    modeIsSelect: boolean = true;
    fileSub: Subscription;
    projectSub: Subscription;
    jobSub: Subscription;
    showGenePasteArea: boolean = false;
    uploadingDemoFile: boolean = false;
    
    sortColumn: string = "datetime";
    sortReverse: boolean = false;
    selectedRowIndex: number = null;
    
    //jobs
    jobs: Job[] = null;
    allJobs: Job[] = null;
    jobFolderStates = new Map<number, boolean>();
    //output files produced by running a job
    allJobOutputFiles = new Map<number, NestFile[]>();
    jobOutputFiles = new Map<number, NestFile[]>();
    //tags
    selectedTag: string = 'all';

    // Our demo file metadata is stored in client/data/demofiles.json
    private demoFilesUrl = '/static/data/demofiles.json';
    private demoFiles: any = {};

    constructor(
        private _router: Router,
        private _http: Http,
        private _jobService: JobService,
        private _fileService: FileService,
        private _projectService: ProjectService,
        private _pipelineService: PipelineService,
        private _sessionService: SessionService,
        private _statusService: ServerStatusService,
        private _logger: LogService,
        private _scrollSettings: SlimScrollSettings,
        private _fileUploadService: FileUploadService,
        private _changeRef: ChangeDetectorRef) {
    }

    ngOnInit(): void {
        // check ISlimScrollOptions for all options
        this.slimScrollOpts = this._scrollSettings.get();
        this.userName = this._sessionService.getDisplayName();
        this.showGenePasteArea = this.fileFormField.allowGenePaste;
        if (this.fileFormField.currentValue) {
            this.selectedIds = this.fileFormField.currentValue.split(",");
        }
        
        this.jobSub = this._jobService.getJobs()
            .catch((error: any) => Observable.throw(error))
            .subscribe(
                (jobs: Array<Job>) => {
                    // sort jobs by date
                    this.allJobs = this.jobs = jobs.slice().sort((a: Job, b: Job) => {
                        return d3.descending(a.getCreatedDate().getTime(), b.getCreatedDate().getTime());
                    });
                    this.resort();
                    this.jobs.forEach((job: Job) => {
                        // don't clear previous states--job service might be polling
                        // while user is working with expanded jobs
                        if (!this.jobFolderStates.has(job._id)) {
                            this.jobFolderStates.set(job._id, false);
                        }
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
        this.fileSub = this._fileService.getFiles().subscribe(
            (files: Array<NestFile>) => {
                this.allFileList = files.slice().sort((a: NestFile, b: NestFile) => {
                    return d3.ascending(a.filename.toUpperCase(), b.filename.toUpperCase());
                });
                if (this.uploadingDemoFile) {
                    let pendingDemoFiles = this.selectDemoFilesAndReturnPending();
                    if (pendingDemoFiles.length == 0) {
                        this.uploadingDemoFile = false;
                    }
                }
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
                if(this.fileFormField.currentValue)
                    this.selectedIds = this.fileFormField.currentValue.split(",");
            }
            if (propName == 'formData') {
                if (this.formData) {
                    this.fileFormField.setData(this.formData);
                    if (this.fileFormField.currentValue == undefined)
                        this.selectedIds = [];
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
        var selectedIdSet = d3.set(this.selectedIds);
        if (selectedIdSet.has(item._id.toString())) {
            if (this.fileFormField.allowMultiSelect) {
                selectedIdSet.remove(item._id.toString());
                this.selectedIds = selectedIdSet.values();
                this.fileFormField.currentValue = this.selectedIds.join();
            } else {
                this.selectedIds = [];
                this.fileFormField.currentValue = null;
            }

        } else {
            if (!this.fileFormField.allowMultiSelect) {
                this.selectedIds = [];
            }
            this.selectedIds.push(item._id.toString());
            this.fileFormField.currentValue = this.selectedIds.join();
        }
        this._changeRef.detectChanges();
    }

    isSelectedFile(file: NestFile): boolean {
        return d3.set(this.selectedIds).has(file._id.toString());
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

    // translate pipeline+field => demo file
    getDemoFiles(): DemoFile[] {
        // Retrieve our demo files for this stage of the pipeline
        let pipelineDemoFiles: any = this.demoFiles[this.pipeline.slug];
        let demoFiles = <DemoFile[]> pipelineDemoFiles[this.fileFormField.dbName];
        return demoFiles;
    }

    isDemoFile(filename: string): boolean {
        if (!this.demoFiles || !this.demoFiles[this.pipeline.slug]) {
            return false;
        }

        // In UI, compare filename to known demo filenames to display "Demo Files" badge
        let demoFiles = this.getDemoFiles();
        return undefined !== demoFiles.find((demoFile) => demoFile.filename == filename);
    }

    useDemoData() {
        let pendingDemoFiles = this.selectDemoFilesAndReturnPending();
        if (pendingDemoFiles.length > 0) {
            this.uploadingDemoFile = true;
            pendingDemoFiles.forEach((demoFile) => {
                this._fileService.copyDemoFile(
                    demoFile.filename, this._projectService.getDefaultProject()._id);
            });
        }
    }

    /**
     * For each demo file associated with the current stage...
     * - ensures any files already loaded are selected
     * - returns the DemoFile objects for any files not already loaded, or an
     *   empty array if all are loaded
     */
    selectDemoFilesAndReturnPending(): DemoFile[] {
        let demoFiles = this.getDemoFiles();
        let loadedFileNameToLoadedFile = d3.map(this.allFileList, (file) => file.filename);
        let selectedIdSet = d3.set(this.selectedIds);
        let returnVal: DemoFile[] = [];

        demoFiles.forEach(demoFile => {
            if (loadedFileNameToLoadedFile.has(demoFile.filename)) {
                let loadedFile = loadedFileNameToLoadedFile.get(demoFile.filename);
                if (!selectedIdSet.has(loadedFile._id.toString())) {
                    this.toggleItem(loadedFile);
                }
            } else {
                returnVal.push(demoFile);
            }
        });
        return returnVal;
    }
    
    /**
     * Help function to sort the data table by name, datetime, size or job status
     **/  
    sort(column: string) {
        if (column == this.sortColumn) {
            this.sortReverse = !this.sortReverse;
        } else {
            this.sortReverse = false;
            this.sortColumn = column;
        }
        if (column === 'name') {
            this.sortFilesByName(this.regularFiles);
            this.sortJobsByName(this.jobs); 
            this.jobOutputFiles.forEach( (value: NestFile[], key: number, map: Map<number, NestFile[]>) => {
                this.sortFilesByName(value);
            });
        } else if (column === 'datetime') {
            this.sortFilesByDate(this.regularFiles);
            this.sortJobsByDate(this.jobs);
            this.jobOutputFiles.forEach((value: NestFile[], key: number, map: Map<number, NestFile[]>) => {
                this.sortFilesByDate(value);
            });
        } else if (column === "size") {
            this.sortFilesBySize(this.regularFiles);
            //ignore jobs since they don't have "size"
            this.jobOutputFiles.forEach((value: NestFile[], key: number, map: Map<number, NestFile[]>) => {
                this.sortFilesBySize(value);
            });
        } else if (column === 'status') {
            //ignore files since they don't have "status"
            this.jobs = this.jobs.sort((a: Job, b: Job) => this.sortReverse ? 
                d3.ascending(a.status.toLowerCase(), b.status.toLowerCase())
                    : d3.descending(a.status.toLowerCase(), b.status.toLowerCase()));
        } 
    }
    
    sortFilesByDate(files: NestFile[]) {
        files.sort((a: NestFile, b: NestFile) => this.sortReverse ? 
            d3.ascending(a.getCreatedDate().getTime(), b.getCreatedDate().getTime())
                : d3.descending(a.getCreatedDate().getTime(), b.getCreatedDate().getTime()));
    }
    
    sortFilesByName(files: NestFile[]) {
        files.sort((a: NestFile, b: NestFile) => this.sortReverse ?
            d3.ascending(a.filename.toLowerCase(), b.filename.toLowerCase())
                : d3.descending(a.filename.toLowerCase(), b.filename.toLowerCase()));
    }
    
    sortFilesBySize(files: NestFile[]) {
        files.sort((a: NestFile, b: NestFile) => this.sortReverse ?
            d3.ascending(a.filesize, b.filesize) : d3.descending(a.filesize, b.filesize));
    }
    
    sortJobsByDate(jobs: Job[]) {
        jobs.sort((a: Job, b: Job) => this.sortReverse ? 
            d3.ascending(a.getCreatedDate().getTime(), b.getCreatedDate().getTime())
                : d3.descending(a.getCreatedDate().getTime(), b.getCreatedDate().getTime()));
    }
    
    sortJobsByName(jobs: Job[]) {
        jobs.sort((a: Job, b: Job) => this.sortReverse ? 
            d3.ascending(a.name.toLowerCase(), b.name.toLowerCase())
                : d3.descending(a.name.toLowerCase(), b.name.toLowerCase()));
    }
    
    selectTag(tagName: string = "") {
        this.selectedTag = tagName;
        this.resort();
    }
    
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
    
    /**
     * open or close job folder to show or hide job output files
     */
    toggleJobFolderState(job_id: number) {
        this.jobFolderStates.set(job_id, !this.jobFolderStates.get(job_id));
    }

    /**
     * Given a job id, Return list of output files associated with this job
     */
    getJobOutputFiles(job_id: number): NestFile[] {
        return this.allFileList.filter(file => file.job_id == job_id)
    }
}

interface DemoFile {
    filename: string;
}