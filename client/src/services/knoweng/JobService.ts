import {Injectable} from '@angular/core';
import {Headers} from '@angular/http';
import {AuthHttp} from 'angular2-jwt';
import {Observable} from 'rxjs/Observable';
import {Subscription} from 'rxjs/Subscription';
import {BehaviorSubject} from 'rxjs/BehaviorSubject';

import 'rxjs/add/operator/share';

import {Job} from '../../models/knoweng/Job';
import {DownloadUtilities} from '../common/DownloadUtilities';
import {FileService} from './FileService';
import {LogService} from '../common/LogService';
import {SessionService} from '../common/SessionService';

@Injectable()
export class JobService {

    // TODO remove the filter when results are removed from the jobs schema
    private _jobUrl: string = '/api/v2/jobs';
    private _jobDownloadUrl: string = '/api/v2/job_downloads';
    // a stream of the current Job[], initialized to []
    private _jobsSubject: BehaviorSubject<Job[]> = new BehaviorSubject<Job[]>([]);

    // Save our current job fetch subscription, so we can ensure it is cleaned up properly
    private _jobSub: Subscription;

    private static LONG_INTERVAL: number = 300000;
    private static SHORT_INTERVAL: number = 5000;

    private _timeout: any;

    constructor(
        private authHttp: AuthHttp,
        private fileService: FileService,
        private logger: LogService,
        private sessionService: SessionService) {
        // as soon as we have an authentication token, or whenever the token
        // changes, fetch data

        this.sessionService.tokenChanged()
            .catch((error: any) => Observable.throw(error))
            .subscribe(
                (data: any) => this.triggerFetch(),
                (err: any) => this.logger.error("JobService failed to refresh token")
            );
    }

    /**
     * Returns a stream of the current Job[].
     */
    getJobs(): Observable<Job[]> {
        return this._jobsSubject.asObservable();
    }

    /**
     * Returns a stream consisting of a single Job object.
     */
    getJob(jobId: string): Observable<Job> {
        return this.getJobs()
            .map(jobs => {
                // Short-circuit for the race condition where we request
                // a job by id before the full list has loaded
                if (!jobs || !jobs.length) {
                    return null;
                }

                // Filter existing job list by jobId
                let results = jobs.filter((job: Job) => job._id.toString() === jobId);
                if (!results.length || results.length > 1) {
                    this.logger.warn(`WARNING: getJob found ${results.length} results for job: ${jobId}`);
                }

                // Return first match
                return results[0];
            });
     }
     
     getJobByIdSync(id: number): Job {
        let returnVal: Job = this._jobsSubject.getValue().find((job: Job) => job._id === id);
        if (returnVal === undefined) {
            this.logger.warn('WARNING: User requested a nonexistent job id (' + id + ')... returning undefined');
        }
        return returnVal;
    }

    /**
     * Deletes a job.
     */
    deleteJob(job: Job): void {
        var headers = new Headers();
        var requestStream = this.authHttp
            .delete(this._jobUrl + '/' + job._id, {
                headers: headers
            })
            .catch((error: any) => Observable.throw(error));
        requestStream.subscribe(
            res => {
                this.triggerFetch();
            },
            err => {
                //If the targeted job is not found, e.g HTTP code 404 NOT FOUND, we will not throw any error.
                if (err.status != 404) {
                    this.logger.error("Failed to delete job: " + job._id);
                }
            }
        );
    }

    /**
     * Fetches the current jobs from the server.
     */
    triggerFetch() {
        // Ensure that any old job subscription is cleaned up before starting a new one
        if (this._jobSub) {
            this._jobSub.unsubscribe();
            this._jobSub = null;
        }

        // fetch the current jobs from the server
        let requestStream = this.authHttp
            .get(this._jobUrl)
            .map(res => {
                let jobsData: any[] = res.json()._items;
                return jobsData.map((jobDatum: any) => new Job(jobDatum));
            });

        // add the array from the server to the stream of current jobs
        // if any jobs are still running, schedule another fetch
        this._jobSub = requestStream
            .catch((error: any) => Observable.throw(error))
            .subscribe(
                jArr => {
                    
                    // ==
                    // determine whether anything changed
                    // ==
                    // getStatusKeyArray: given an array of jobs, returns an
                    // array of "status key" strings, each of which combines
                    // the job id and status
                    let getStatusKeyArray = (jobs: Job[]) => {
                        return jobs.map((job) => job._id + ":" + job.status);
                    };
                    // lastSet: a set of the status keys from the previous
                    // response from the jobs endpoint
                    let lastSet = new Set<string>(
                        getStatusKeyArray(this._jobsSubject.getValue()));
                    // thisArray: an array of the status keys from this response
                    // from the jobs endpoint
                    let thisArray = getStatusKeyArray(jArr);
                    // same: true if and only if lastSet and thisArray have the
                    // same number of items and every element of thisArray
                    // appears in lastSet
                    let same = thisArray.reduce(
                        (acc, current) => acc && lastSet.has(current),
                        lastSet.size == thisArray.length
                    );
                    //the equality check above only checks status, but we could also do better by checking other updatable job attributes like name, favorite and notes
                    //if we do that, we don't need to update job subject here, but only to update when !same
                    this._jobsSubject.next(jArr);
                    if (!same) {
                        this.fileService.triggerFetch();
                    }

                    let hasRunning: boolean = jArr.some((job: Job) => {
                        return job.status == "running";
                    });

                    if (this._timeout) {
                        clearTimeout(this._timeout);
                        this._timeout = null;
                    }
                    let period = hasRunning ? JobService.SHORT_INTERVAL : JobService.LONG_INTERVAL;
                    this._timeout = setTimeout(() => this.triggerFetch(), period);
                },
                err => {
                    this.logger.error("Failed fetching jobs");
                });
    }

    /**
     * job: the Job object to POST to the server
     */
    createJob(job: Job): Observable<Job> {
        var headers = new Headers();
        headers.append('Content-Type', 'application/json');
        var payload: any = {status: "running"} // TODO improve job status state machine
        // only send non-null fields
        for (var field of Job.getFields()) {
            if ((<any>job)[field] !== null) {
                payload[field] = (<any>job)[field];
            }
        }
        // post the new file to the server
        // note we share() the stream so we only POST once, no matter how many
        // subscribers--important here because we return the observable
        var url = this._jobUrl + '?reply=whole'
        var requestStream = this.authHttp
            .post(
                url,
                JSON.stringify(payload),
                {headers: headers}
            )
            .catch((error: any) => Observable.throw(error))
            .map(res => {
                //var eveAttrs: any = res.json();
                var newJob: Job = new Job(res.json()); // don't modify caller's object
                //newJob.mergeEveAttributes(eveAttrs);
                return newJob;
            }).share();
        // add the new job to the current Job[] and publish the updated
        // Job[] to the _jobsSubject stream
        requestStream.subscribe(
            job => {
                var currentJobs = this._jobsSubject.getValue();
                currentJobs.push(job);
                this._jobsSubject.next(currentJobs);
                this.triggerFetch(); // start monitoring the jobs endpoint again
            },
            err => {
                this.logger.error("Failed creating job: " + job.name);
            });
        return requestStream;
    }

    /**
     * Given a file, return the URL to download that file
     */
    getDownloadUrl(job: Job): string {
        return this._jobDownloadUrl + '/' + job._id;
    }

    /**
     * Downloads a job.
     */
    downloadJob(job: Job): Observable<string> {
        return DownloadUtilities.downloadFile(this.getDownloadUrl(job), this.authHttp);
    }

    /**
     * Update job notes field and return updated job back to client if successful
     */
    updateJobNotes(job: Job, newNotes: string): Observable<Job> {
        let url = this._jobUrl + '/' + job._id + '?reply=whole';
        let headers = new Headers();
        headers.append('Content-Type', 'application/json');
        var payload = {notes: newNotes};
        var requestStream = this.authHttp
            .patch(
                url,
                JSON.stringify(payload),
                {headers: headers}
            )
            .catch((error: any) => Observable.throw(error))
            .map(res => {
                //var eveAttrs: any = res.json();
                var newJob: Job = new Job(res.json());
                //newJob.notes = newNotes;
                //newJob.mergeEveAttributes(eveAttrs);
                return newJob;
            }).share();
        //need to fetch jobs so the result table will include the job that was just updated
         requestStream.subscribe(
            job => {
                this.triggerFetch();
            },
            err => {
                this.logger.error("Failed to update job notes: " + job._id);
            });
        return requestStream;
    }

    /**
     * Update job favorite field and return updated job back to client if successful
     */
    updateJobFavorite(job: Job, newFavorite: boolean): Observable<Job> {
        let url = this._jobUrl + '/' + job._id + '?reply=whole';
        let headers = new Headers();
        headers.append('Content-Type', 'application/json');
        var payload = {favorite: newFavorite};
        var requestStream = this.authHttp
            .patch(
                url,
                JSON.stringify(payload),
                {headers: headers}
            )
            .catch((error: any) => Observable.throw(error))
            .map(res => {
                //var eveAttrs: any = res.json();
                var newJob: Job = new Job(res.json());
                //newJob.favorite = newFavorite;
                //newJob.mergeEveAttributes(eveAttrs);
                return newJob;
            }).share();
        //need to fetch jobs so the result table will include the job that was just updated
         requestStream.subscribe(
            job => {
                this.triggerFetch();
            },
            err => {
                this.logger.error("Failed to update job favorites: " + job._id);
            });
        return requestStream;
    }
    
     /**
     * Update job name field and return updated job back to client if successful
     */
    updateJobName(job: Job, newName: string): Observable<Job> {
        let url = this._jobUrl + '/' + job._id + '?reply=whole';
        let headers = new Headers();
        headers.append('Content-Type', 'application/json');
        var payload = {name: newName};
        var requestStream = this.authHttp
            .patch(
                url,
                JSON.stringify(payload),
                {headers: headers}
            )
            .catch((error: any) => Observable.throw(error))
            .map(res => {
                //var eveAttrs: any = res.json();
                var newJob: Job = new Job(res.json());
                //newJob.favorite = newFavorite;
                //newJob.mergeEveAttributes(eveAttrs);
                return newJob;
            }).share();
        //need to fetch jobs so the result table will include the job that was just updated
         requestStream.subscribe(
            job => {
                this.triggerFetch();
            },
            err => {
                this.logger.error("Failed to update job name: " + job._id);
            });
        return requestStream;
    }
}
