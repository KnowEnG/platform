import {ChangeDetectorRef, Component, OnInit, OnChanges, EventEmitter, Input, Output, SimpleChange} from '@angular/core';
import {Router} from '@angular/router';

import {Subscription} from 'rxjs/Subscription';

import {Project} from '../../../../models/knoweng/Project';
import {Result} from '../../../../models/knoweng/results/SampleClustering';
import {Job} from '../../../../models/knoweng/Job';
import {NestFile} from '../../../../models/knoweng/NestFile';
import {Form, FormData, FormGroup, FormField, HiddenFormField, FieldSummary} from '../../../../models/knoweng/Form';

import {LogService} from '../../../../services/common/LogService';
import {JobService} from '../../../../services/knoweng/JobService';
import {PipelineService} from '../../../../services/knoweng/PipelineService';
import {ProjectService} from '../../../../services/knoweng/ProjectService';
import {SessionService} from '../../../../services/common/SessionService';

@Component({
    moduleId: module.id,
    selector: 'job-summary',
    templateUrl: './JobSummary.html',
    styleUrls: ['./JobSummary.css']
})

export class JobSummary implements OnInit, OnChanges {
    class = 'relative';

    @Input()
    job: Job;
    
    /** Unused currently but expected soon. */
    @Input()
    result: Result;
    
    @Input()
    currentProject: Project = null;
    
    /* Can be 'vertical' (GP / GSC) or 'horizontal' (SC) */
    @Input()
    orientation: string = 'vertical';
    
    form: Form = null;
    formSub: Subscription = null;

    @Output()
    changeProject: EventEmitter<Project> = new EventEmitter<Project>();

    modal: string = null;
    modalBottom: number = 0;
    modalRight: number = 0;
    
    maxLength: number = 35;

    projectList: Project[] = [];
    projectSub: Subscription;
        
    summaries: FieldSummary[] = [];

    constructor(private _logger: LogService, 
                private _pipelineService: PipelineService, 
                private _jobService: JobService, 
                private _projectService: ProjectService,
                private _sessionService: SessionService,
                private _router: Router,
                private _changeDetector: ChangeDetectorRef) {
    }
    ngOnInit() {
        this.projectSub = this._projectService.getProjects().subscribe(
            (projects: Array<Project>) => {
                this.projectList = projects.slice().sort((a: Project, b: Project) => {
                    return d3.ascending(a.name.toUpperCase(), b.name.toUpperCase());
                });
                // initialize if parent didn't provide a currentProject
                if (this.currentProject === null && this.projectList.length > 0) {
                    this.onChangeProjectId(this.projectList[0]._id);
                }
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
    }
    ngOnDestroy() {
        this.projectSub.unsubscribe();
        if (this.formSub !== null) {
            this.formSub.unsubscribe();
        }
    }
    ngOnChanges(changes: {[propertyName: string]: SimpleChange}) {
        for (let propName in changes) {
            if (propName === 'job' && this.job) {
                if (this.formSub !== null) {
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
            }
        }
    }
    
    openModal(event: Event, modal: string): void {
        this.modal = modal;
        this.modalBottom = window.innerHeight - (<any>event).clientY - 85; // 85 looks good on the screen; no science to it
        if (this.modalBottom < 0) {
            this.modalBottom = 0;
        }
        this.modalRight = window.innerWidth - (<any>event).clientX - 15; // 15 looks good on the screen; no science to it
    }
    
    updateNotes(notes: string): void {
        this._jobService.updateJobNotes(this.job, notes).subscribe(job => this.job = job);
        this.modal = null;
    }
    
    closeModal(event: Event): void {
        this.modal = null;
    }
    
    /** FIXME: Currently just a stub - does not call out to /api */
    onChangeProjectId(projectId: number) : void {
       // pull the currentProject out of this.projectList
       this.currentProject = this.projectList.filter((project: Project) => project._id == projectId)[0];
       this.changeProject.emit(this.currentProject);
    }
    
    /** FIXME: Currently just a stub - does not call out to /api */
    onChangeJobName(jobName: string): void {
        this.form.jobName = name;
    }
}
