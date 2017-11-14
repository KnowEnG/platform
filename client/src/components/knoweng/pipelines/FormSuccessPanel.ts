import {Component, OnChanges, OnDestroy, SimpleChange, Input, Output, EventEmitter} from '@angular/core';
import {Router} from '@angular/router';

import {Observable} from 'rxjs/Observable';
import {Subscription} from 'rxjs/Subscription';
import {SessionService} from '../../../services/common/SessionService';
import {JobService} from '../../../services/knoweng/JobService';
import {Form} from '../../../models/knoweng/Form';
import {Job} from '../../../models/knoweng/Job';

@Component({
    moduleId: module.id,
    selector: 'form-success-panel',
    templateUrl: './FormSuccessPanel.html',
    styleUrls: ['./FormSuccessPanel.css']
})

export class FormSuccessPanel implements OnChanges, OnDestroy {
    class = 'relative';

    @Input()
    form: Form = null; // defines form
    
    @Input()
    submittedJobId: number = null;

    @Output()
    restart: EventEmitter<Form> = new EventEmitter<Form>();
    
    submittedJobStatus: string = null;
    jobSub: Subscription = null;

    constructor(private _router: Router,
                private _jobService: JobService,
                private _sessionService: SessionService) {
    }
    ngOnChanges(changes: {[propertyName: string]: SimpleChange}) {
        if (this.jobSub) {
            this.jobSub.unsubscribe();
            this.jobSub = null;
        }
        
        if(this.submittedJobId) {
            this.jobSub = this._jobService.getJobs()
                .catch((error: any) => Observable.throw(error))
                .subscribe(
                    (jobs: Array<Job>) => {
                        //find the matching job's status
                        var sji = this.submittedJobId;
                        var sjs: string = null; 
                        jobs.map(function(job) {
                            if (job._id == sji)
                                sjs = job.status;
                        });
                        this.submittedJobStatus = sjs;
                    },
                    (error: any) => {
                        if (error.status == 401) {
                            this._sessionService.redirectToLogin();
                        } else {
                            alert(`Server error. Try again later`);
                        }
                    });
        }
    }
    ngOnDestroy() {
        if (this.jobSub) {
            this.jobSub.unsubscribe();
            this.jobSub = null;
        }
    }
    onClickRestart(): void {
        this.restart.emit(this.form);
    }
    onClickResults(): void {
        // TODO replace with routerLink in template after ng2 update
        this._router.navigate( ['/results'] );
    }
}
