import {Component, OnInit, OnChanges, SimpleChange, Input, Output, EventEmitter} from '@angular/core';
import {Router} from '@angular/router';
import {Subscription} from 'rxjs/Subscription';

import {Form, FormData, FormGroup, FormField, FieldSummary, HiddenFormField} from '../../../models/knoweng/Form';
import {Project} from '../../../models/knoweng/Project';
import {ProjectService} from '../../../services/knoweng/ProjectService';
import {LogService} from '../../../services/common/LogService';
import {SessionService} from '../../../services/common/SessionService';

@Component({
    moduleId: module.id,
    selector: 'form-review-panel',
    templateUrl: './FormReviewPanel.html',
    styleUrls: ['./FormReviewPanel.css']
})

export class FormReviewPanel implements OnInit, OnChanges {
    class = 'relative';

    @Input()
    form: Form = null; // defines form

    @Input()
    currentProject: Project = null;

    @Output()
    changeProject: EventEmitter<Project> = new EventEmitter<Project>();

    summaries: FieldSummary[] = [];

    modal: string = null;
    modalBottom: number = 0;
    modalRight: number = 0;

    projectList: Project[] = [];
    projectSub: Subscription;

    constructor(
        private _router: Router,
        private _projectService: ProjectService,
        private _sessionService: SessionService,
        private _logger: LogService) {
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
    }
    ngOnChanges(changes: {[propertyName: string]: SimpleChange}) {
        this.summaries = [];
        let formData: FormData = this.form.getData();
        this.form.formGroups.forEach((group: FormGroup) => {
            group.fields.forEach((field: FormField) => {
                if (field.isEnabled(formData) && !(field instanceof HiddenFormField)) {
                    this.summaries = this.summaries.concat(field.getSummary());
                }
            });
            this.summaries.push(null);
        });
    }
    openModal(event: Event, modal: string): void {
        this.modal = modal;
        this.modalBottom = window.innerHeight - (<any>event).clientY - 85; // 85 looks good on the screen; no science to it
        if (this.modalBottom < 0) {
            this.modalBottom = 0;
        }
        this.modalRight = window.innerWidth - (<any>event).clientX - 15; // 15 looks good on the screen; no science to it
    }
    closeModal(event: Event): void {
        this.modal = null;
    }
    saveCloseNotesModal(newNotes: string): void {
        this.form.notes = newNotes;
        this.modal = null;
    }
    onChangeProjectId(projectId: number) : void {
       // pull the currentProject out of this.projectList
       this.currentProject = this.projectList.filter((project: Project) => project._id == projectId)[0];
       this.changeProject.emit(this.currentProject);
    }
    setJobName(name: string): void {
        this.form.jobName = name;
    }
    
    /**
     * To check is a form field value is multiple values delimted by ",". An example of this is the multiple primary/secondary 
     * file names with spreadsheet visualization. 
     */
    isMultiValues(summaryValue: string) {
        if (summaryValue) {
            let valueArray = summaryValue.split(",");
            return valueArray.length > 1; 
        }
        return false;
    }
    
    /**
     * Delimite multiple value (file names) string into array to display one (file name) per line
     */
    getMultiValues(values: string) {
        return values.split(",");
    }
}
