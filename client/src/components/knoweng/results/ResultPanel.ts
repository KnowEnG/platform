import {ChangeDetectorRef, Component, OnInit, OnChanges, SimpleChange, Input, Output, EventEmitter, ElementRef, ViewChild, AfterViewChecked} from '@angular/core';
import { ISlimScrollOptions } from 'ng2-slimscroll';

import {Observable} from 'rxjs/Observable';
import {Subscription} from 'rxjs/Subscription';

import {Form, FormData, FormGroup, FormField, HiddenFormField, FieldSummary} from '../../../models/knoweng/Form';
import {Job} from '../../../models/knoweng/Job';
import {NestFile} from '../../../models/knoweng/NestFile';
import {JobService} from '../../../services/knoweng/JobService';
import {FileService} from '../../../services/knoweng/FileService';
import {PipelineService} from '../../../services/knoweng/PipelineService';
import {ProjectService} from '../../../services/knoweng/ProjectService';
import {SlimScrollSettings} from '../../../services/common/SlimScrollSettings';
import {LogService} from '../../../services/common/LogService';

@Component({
    moduleId: module.id,
    selector: 'result-panel',
    templateUrl: './ResultPanel.html',
    styleUrls: ['./ResultPanel.css']
})

export class ResultPanel implements OnInit, OnChanges, AfterViewChecked {
    class = 'relative';

    public slimScrollOpts: ISlimScrollOptions;

    @Input()
    job: Job;
    
    @Output()
    jobOpened: EventEmitter<Job> = new EventEmitter<Job>();
    
    @ViewChild('newjobnameinput') newjobnameinput: ElementRef;

    modal: string = null;
    modalBottom: number = 0;
    modalRight: number = 0;
    formSub: Subscription;
    featuresFileName: string = "";
    responseFileName: string = "";
    geneSpreadsheetName: string = "";
    projectName: string = "";
    summaries: FieldSummary[] = [];
    downloadStatus: string = '';
    isEditable: boolean = false;
    newJobName: string = null;

    constructor(
        private _jobService: JobService,
        private _fileService: FileService,
        private _pipelineService: PipelineService,
        private _projectService: ProjectService,
        private _scrollSettings: SlimScrollSettings,
        private _logger: LogService,
        private _changeDetector: ChangeDetectorRef) {
    }
    ngOnInit() {
        // check ISlimScrollOptions for all options
        this.slimScrollOpts = this._scrollSettings.get();
    }
    ngOnDestroy() {
        if (this.formSub) {
            this.formSub.unsubscribe();
        }
    }
    ngOnChanges(changes: {[propertyName: string]: SimpleChange}) {
        for (let propName in changes) {
            if (propName === 'job' && this.job && (!changes['job'].previousValue || this.job._id !== changes['job'].previousValue._id)) {
                if (this.formSub) {
                    this.formSub.unsubscribe();
                }
                // Load our pipeline Form
                this.formSub = this._pipelineService.getPipelineBySlug(this.job.pipeline).getForm().subscribe(form => {
                    this.summaries = [];
                    
                    let formData = FormData.fromParametersObject(this.job.parameters);
                    form.setData(formData);
                    form.formGroups.forEach((group: FormGroup) => {
                        group.fields.forEach((field: FormField) => {
                            // TODO: Handle case: "null" response file
                            if (field.isEnabled(formData) && !(field instanceof HiddenFormField)) {
                                // Add this summary to our running list
                                Array.prototype.push.apply(this.summaries, field.getSummary());
                            }
                        });
                
                        // Push a "null" item to simulate a line break between groups
                        this.summaries.push(null);
                    });
                    // trigger another round of change detection--for some reason, couldn't
                    // eliminate zone error when using observable and async pipe
                    this._changeDetector.detectChanges();
                });
                
                // Populate features file name based on file id
                // FIXME: We shouldnt need to explicitly query for these, as they should be included in the form summaries list
                // using parseInt because file ids are saved as strings in the launcher; TODO revisit when modeling nest IDs
                let fid: number = parseInt(this.job.parameters.features_file, 10);
                if (fid) {
                    this._fileService.getFileById(fid).subscribe((result: NestFile) => {
                        this.featuresFileName = NestFile.getFileNameOrPlaceholder(result);
                    });
                }
                
                // Populate response file name based on file id
                // FIXME: We shouldnt need to explicitly query for these, as they should be included in the form summaries list
                let rid: number = parseInt(this.job.parameters.response_file, 10);
                if (rid) {
                    this._fileService.getFileById(rid).subscribe((result: NestFile) => {
                        this.responseFileName = NestFile.getFileNameOrPlaceholder(result);
                    });
                }
                
                // Populate gene spreadsheet file name based on file id
                // FIXME: We shouldnt need to explicitly query for these, as they should be included in the form summaries list
                let gid: number = parseInt(this.job.parameters.gene_set_file, 10);
                if (gid) {
                    this._fileService.getFileById(gid).subscribe((result: NestFile) => {
                        this.geneSpreadsheetName = NestFile.getFileNameOrPlaceholder(result);
                    });
                }
                
                let project = this._projectService.getProject(this.job.project_id);
                if (project) {
                    this.projectName = project.name;
                }
                this.newJobName = this.job.name;
            }
        }
    }
    /**
     * After the job renaming input text field is created, highlight the whole text.
     */
    ngAfterViewChecked() {
        if(this.newjobnameinput) {
            let input = this.newjobnameinput.nativeElement;
            input.focus();
            let inputText = input.value;
            if (inputText == this.job.name) {
                if(input.setSelectionRange) {
                    input.setSelectionRange(0, inputText.length);
                } else if (input.createTextRange) {
                    var range = input.createTextRange();
                    range.collapse(true);
                    range.moveEnd('character', inputText.length);
                    range.moveStart('character', 0);
                    range.select();
                }
            }
        } 
    }
    
    deleteJob(): void {
        this._jobService.deleteJob(this.job);
    }
    
    downloadJob(): void {
        var observable: Observable<string> = this._jobService.downloadJob(this.job);
        observable.subscribe ({
            next: status => { 
                this.downloadStatus = status; 
            },
            error: err => { 
                this.downloadStatus = "error";
                this._logger.error(err.message, err.stack);
            },
            complete: () => { 
                this.downloadStatus = "complete"; 
            }
        });
    }
    
    updateFavorite(): void {
        let favorite = this.job.favorite;
        if (favorite == null || favorite == false) {
            this._jobService.updateJobFavorite(this.job, true)
            .subscribe(job => {
                this.job = job;
            });
        } else {
             this._jobService.updateJobFavorite(this.job, false)
            .subscribe(job => {
                this.job = job;
            });
        } 
    }
    
    updateJobName(): void {
        if(this.newJobName && this.newJobName.length > 0) {
            if (this.newJobName != this.job.name) {
                this._jobService.updateJobName(this.job, this.newJobName)
                    .subscribe(job => {
                        this.job = job;
                })
            }  
        } else {
            this.newJobName = this.job.name;
        }
        this.isEditable = false;
    }
    
    openModal(event: Event, modal: string): void {
        this.modal = modal;
        this.modalBottom = window.innerHeight - (<any>event).clientY - 85; // 85 looks good on the screen; no science to it
        if (this.modalBottom < 0) {
            this.modalBottom = 0;
        }
        this.modalRight = window.innerWidth - (<any>event).clientX - 15; // 15 looks good on the screen; no science to it
    }
    
    saveCloseNotesModal(notes: string): void {
        this._jobService.updateJobNotes(this.job, notes)
            .subscribe(job => {
                this.job = job;
            });
        this.modal = null;
    }
    
    closeModal(event: Event): void {
        this.modal = null;
    }
}
