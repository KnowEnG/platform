import {Component, ChangeDetectorRef, OnInit, OnDestroy, OnChanges, SimpleChange, Input, ViewChild} from '@angular/core';
import {Router, ActivatedRoute, Params} from '@angular/router';

import {Subscription} from 'rxjs/Subscription';
import {ModalDirective} from 'ngx-bootstrap';

import {Form, FormData} from '../../../models/knoweng/Form';
import {Job} from '../../../models/knoweng/Job';
import {Pipeline} from '../../../models/knoweng/Pipeline';
import {PipelineService} from '../../../services/knoweng/PipelineService';
import {Project} from '../../../models/knoweng/Project';
import {JobService} from '../../../services/knoweng/JobService';

@Component({
    moduleId: module.id,
    selector: 'form-container',
    templateUrl: './FormContainer.html',
    styleUrls: ['./FormContainer.css']
})

export class FormContainer implements OnInit, OnDestroy, OnChanges {
    class = 'relative';

    @ViewChild(ModalDirective) modal : ModalDirective;

    form: Form = null;
    currentIndex: number = 0;
    saveAsTemplate: boolean = false;
    submitted: boolean = false;
    submittedJobId: number = null;
    pipeline: Pipeline = null;
    
    currentProject: Project = null;

    errorMessage: string = null;
    
    routeSub: Subscription;

    constructor(
        private _changeDetector: ChangeDetectorRef,
        private _jobService: JobService,
        private _pipelineService: PipelineService,
        private _route: ActivatedRoute,
        private _router: Router) {
    }
    ngOnInit() {
        this.routeSub = this._route.params.subscribe((params : Params) => {
            var pipelineSlug = params['id'];
            this.pipeline = this._pipelineService.getPipelineBySlug(pipelineSlug);
            if (this.pipeline === undefined)
                this.onRestart();
            else {
                this.pipeline.getForm().subscribe(form => this.form = form);
            }
        });
    }
    ngOnDestroy() {
        this.routeSub.unsubscribe();
    }
    ngOnChanges(changes: {[propertyName: string]: SimpleChange}) {
    }
    onClickFormGroup(groupIndex: number): void {
        this.currentIndex = groupIndex;
        this._changeDetector.detectChanges();
    }
    groupIndexIsEnabled(groupIndex: number): boolean {
        let returnVal: boolean = true;
        let formData: FormData = this.form.getData();
        for (let i: number = 0; i < groupIndex; i++) {
            returnVal = returnVal && this.form.formGroups[i].isValid(formData);
        }
        return returnVal;
    }
    onClickNext(): void {
        this.currentIndex++;
        this._changeDetector.detectChanges();
    }
    onClickPrevious(): void {
        this.currentIndex--;
        this._changeDetector.detectChanges();
    }
    onRestart(): void {
        this._router.navigate( ['/pipelines'] );
    }
    onClickCancel(): void {
        this.onRestart();
    }
    onChangeProject(project: Project) {
        this.currentProject = project;
    }
    onClickSubmit(): void {
        let parameters: any = {};
        this.form.getData().fieldMap.forEach((key: string, value: any) => {
           parameters[key] = value;
        });
        let job: Job = new Job({
           name: this.form.jobName,
           notes: this.form.notes,
           pipeline: this.pipeline.slug,
           project_id: this.currentProject._id,
           status: "running",
           parameters: parameters
        });
        this.submitted = true; // optimistic; also has benefit of changing UI
                               // in such a way that prevents double-submits
        this._jobService.createJob(job).subscribe(
            (job: Job) => {
                this.submittedJobId = job._id;
            },
            err => {
                this.submitted = false;
                this.errorMessage = err.text();
                this.modal.show();
            }
        );
    }
    onClickSaveTemplate(): void {
        // TODO handle
        this.saveAsTemplate = !this.saveAsTemplate;
    }
}
