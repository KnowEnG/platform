import {Component, OnInit, OnDestroy, EventEmitter, Output} from '@angular/core';
import {Router} from '@angular/router';
import {ISlimScrollOptions} from 'ng2-slimscroll';

import {Observable} from 'rxjs/Observable';
import {Subscription} from 'rxjs/Subscription';

import {JobService} from '../../../services/knoweng/JobService';
import {ProjectService} from '../../../services/knoweng/ProjectService';
import {Job} from '../../../models/knoweng/Job';
import {Project} from '../../../models/knoweng/Project';
import {SessionService} from '../../../services/common/SessionService';
import {LogService} from '../../../services/common/LogService';
import {SlimScrollSettings} from '../../../services/common/SlimScrollSettings';

@Component({
    moduleId: module.id,
    selector: 'results-table',
    templateUrl: './ResultsTable.html',
    styleUrls: ['./ResultsTable.css']
})

export class ResultsTable implements OnInit, OnDestroy {
    class = 'relative';
    
    public slimScrollOpts: ISlimScrollOptions;

    @Output()
    jobSelected: EventEmitter<Job> = new EventEmitter<Job>();

    allJobs: Job[] = null;
    jobs: Job[] = null;
    projects: Project[] = null;
    jobSub: Subscription;
    projectSub: Subscription;
    
    selectedTag: string = 'all';

    constructor(
       private _router: Router,
       private _jobService: JobService,
       private _projectService: ProjectService,
       private _sessionService: SessionService,
       private _logger: LogService,
       private _scrollSettings: SlimScrollSettings) {
    }
    ngOnInit() {
        // check ISlimScrollOptions for all options
        this.slimScrollOpts = this._scrollSettings.get();
        
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
    }
    ngOnDestroy() {
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
    resort(): void {
        let tagName = this.selectedTag;
        if (!tagName || tagName === 'all') {
            this.jobs = this.allJobs.slice();
        } else if (tagName === 'recent') {
            // Figure out the Date 1 week ago
            let oneWeekAgo = new Date();
            oneWeekAgo.setDate(oneWeekAgo.getDate() - 7);
            
            this.jobs = this.allJobs.slice()
                .filter((a: Job) => oneWeekAgo.getTime() < a.getCreatedDate().getTime())
                .sort((a: Job, b: Job) => d3.descending(a.getCreatedDate().getTime(), b.getCreatedDate().getTime()));
        }
    }
}
