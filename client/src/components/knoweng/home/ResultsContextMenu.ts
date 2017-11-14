import {Component, OnInit, Input, EventEmitter, Output} from '@angular/core';
import {Observable} from 'rxjs/Observable';

import {JobService} from '../../../services/knoweng/JobService';
import {LogService} from '../../../services/common/LogService';
import {Job} from '../../../models/knoweng/Job';

@Component({
    moduleId: module.id,
    selector: 'results-context-menu',
    templateUrl: './ResultsContextMenu.html',
    styleUrls: ['./ResultsContextMenu.css']
})

export class ResultsContextMenu implements OnInit {
    class = 'relative';
    
    @Input()
    job: Job;
    
    @Output()
    closeMe: EventEmitter<boolean> = new EventEmitter<boolean> ();
    
    downloadStatus: string = '';
    
    constructor(private jobService: JobService,
                private logger: LogService) {
    }
    
    ngOnInit() {
    }
    
    deleteJob(): void {
        this.jobService.deleteJob(this.job);
        this.closeMe.emit(true);
    }
    
    downloadJob(): void {
        var observable: Observable<string> = this.jobService.downloadJob(this.job);
        observable.subscribe ({
            next: status => { 
                this.downloadStatus = status; 
                this.closeMe.emit(false);
            },
            error: err => { 
                this.downloadStatus = "error";
                this.logger.error(err.message, err.stack);
                this.closeMe.emit(true);
            },
            complete: () => { 
                this.downloadStatus = "complete"; 
                this.closeMe.emit(true);
            }
        });
       
    }
    
    updateFavorite(): void {
        let favorite = this.job.favorite;
        if (favorite == null || favorite == false) {
            this.jobService.updateJobFavorite(this.job, true)
            .subscribe(job => {
                this.job = job;
            });
        } else {
             this.jobService.updateJobFavorite(this.job, false)
            .subscribe(job => {
                this.job = job;
            });
        } 
        this.closeMe.emit(true);
    }
}
