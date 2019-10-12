import {Component, OnChanges, SimpleChanges, Input, EventEmitter, Output} from '@angular/core';
import {Router, ActivatedRoute } from '@angular/router';
import {Subscription} from 'rxjs/Subscription';
import {FileItem} from 'ng2-file-upload';
import {ISlimScrollOptions} from 'ng2-slimscroll';

import {NestFile} from '../../../models/knoweng/NestFile';
import {Project} from '../../../models/knoweng/Project';
import {Job} from '../../../models/knoweng/Job';
import {LogService} from '../../../services/common/LogService';
import {ProjectService} from '../../../services/knoweng/ProjectService';
import {FileService} from '../../../services/knoweng/FileService';
import {SessionService} from '../../../services/common/SessionService';
import {SlimScrollSettings} from '../../../services/common/SlimScrollSettings';

@Component({
    moduleId: module.id,
    selector: 'results-table-body',
    templateUrl: './ResultsTableBody.html',
    styleUrls: ['./ResultsTableBody.css']
})

export class ResultsTableBody implements OnChanges {
    class = 'relative';
    
    public slimScrollOpts: ISlimScrollOptions;
    
    @Input()
    jobs: Job[] = [];
    
    @Input()
    regularFiles: NestFile[] = [];
    
    @Input()
    jobOutputFiles = new Map<number, NestFile[]>();
    
    @Input()
    uploaderQueue: FileItem[] = [];
    
    @Input()
    projectList: Project[] = [];
    
    @Output()
    fileSelected: EventEmitter<NestFile> = new EventEmitter<NestFile>();

    @Output()
    jobSelected: EventEmitter<Job> = new EventEmitter<Job>();

    sortColumn: string = "datetime";
    sortReverse: boolean = false;

    jobFolderStates = new Map<number, boolean>();
    selectedItem: any = {};

    constructor( 
        private _router: Router,
        private _sessionService: SessionService,
        private _fileService: FileService,
        private _projectService: ProjectService,
        private _logger: LogService,
        private _route: ActivatedRoute,
        private _scrollSettings: SlimScrollSettings) {
        }
    
    ngOnInit() {
        // check ISlimScrollOptions for all options
        this.slimScrollOpts = this._scrollSettings.get();
    }
    
    ngOnChanges(changes: SimpleChanges) {
        for (let propName in changes) {
            if (propName == 'jobs') {
                this.jobs.forEach((job) => {
                    // don't clear previous states--job service might be polling while user
                    // is working with expanded jobs
                    if (!this.jobFolderStates.has(job._id)) {
                        this.jobFolderStates.set(job._id, false);
                    }
                    // if the current selection is a job, and it has just now completed,
                    // emit it again so the panel enables the controls only available
                    // on completed jobs
                    if (this.selectedItem["job_id"] === job._id && job.status == 'completed') {
                        // this job is selected and completed
                        // see whether it just changed
                        let previousJobs = changes['jobs'].previousValue as Job[];
                        let staleJobIndex = previousJobs.findIndex((pj) => {
                           return pj._id == job._id && pj.status !== 'completed';
                        });
                        if (staleJobIndex !== -1) {
                            this.jobSelected.emit(job);
                        }
                    }
                });
            }
        }
    }

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
            this.jobOutputFiles.forEach((value: NestFile[], key: number, map: Map<number, NestFile[]>) => {
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
   
    /* Navigate to ResultVisualization on double-click */
    viewResult(index: number) {
        let job = this.jobs[index];
        
        // Only navigate for completed jobs
        if (job.status === 'completed') {
            this._router.navigate(["./" + job._id], {relativeTo: this._route});
        }
    }

    /* trackByFunction implementation for the list of jobs */
    jobTracker(index: number, item: Job): number {
        return item._id;
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
        return this.jobOutputFiles.get(job_id);
    }
    
    selectJobRow(index: number) {
        this.selectedItem = {
            "job_id": this.jobs[index]._id
        };
        this.jobSelected.emit(this.jobs[index]);
    }
    
    selectRegularFileRow(index: number) {
        this.selectedItem = {
            "file_id": this.regularFiles[index]._id
        };
        this.fileSelected.emit(this.regularFiles[index]);
    }
    
    selectOutputFileRow(jobid: number, index: number) {
        this.selectedItem = {
            "file_id": this.jobOutputFiles.get(jobid)[index]._id
        };
        this.fileSelected.emit(this.jobOutputFiles.get(jobid)[index]);
    }
    
    isJobSelected(jobId: number) {
        return this.selectedItem["job_id"] && this.selectedItem["job_id"] == jobId;
    }
    
    isFileSelected(fileId: number) {
        return this.selectedItem["file_id"] && this.selectedItem["file_id"] == fileId;
    }
}
