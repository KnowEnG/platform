import {Injectable} from '@angular/core';
import {AuthHttp} from 'angular2-jwt';
import {Observable} from 'rxjs/Observable';

import {SignatureScores, SampleScores, Result} from '../../models/knoweng/results/SignatureAnalysis';
import {EveUtilities} from '../common/EveUtilities';
import {LogService} from '../common/LogService';

@Injectable()
export class SignatureAnalysisService {

    private _saResultsUrl: string = '/api/v2/signature_analyses';

    constructor(private authHttp: AuthHttp, private logger: LogService) {
    }

    /**
     * Returns the Result for a specified jobId.
     *
     * Args:
     *     jobId (number): The jobId associated with the Result to fetch.
     *
     * Returns:
     *      Observable<Result> that'll publish a single Result.
     */
    getResult(jobId: number): Observable<Result> {
        var url: string = this._saResultsUrl + "?job_id=" + jobId;
        return this.authHttp
            .get(url)
            .map(res => {
                let items: any[] = res.json()._items;
                let returnVal: Result = null;
                if (items.length == 1) {
                    let item: any = items[0];
                    returnVal = new Result(jobId, new SignatureScores(item.scores));
                } else {
                    this.logger.warn("got " + items.length + " results for " + jobId);
                }
                return returnVal;
            });
    }
}
