import {Injectable} from '@angular/core';
import {AuthHttp} from 'angular2-jwt';
import {Observable} from 'rxjs/Observable';

import {Result} from '../../models/knoweng/results/SampleClustering';
import {LogService} from '../common/LogService';

@Injectable()
export class SampleClusteringService {

    private _scResultsUrl: string = '/api/v2/sample_clusterings';

    constructor(private authHttp: AuthHttp, private logger: LogService) {
    }

    /**
     * Returns the Result for a specified jobId.
     *
     * Args:
     *     jobId (string): The jobId associated with the Result to fetch.
     *
     * Returns:
     *      Observable<Result> that'll publish a single Result.
     */
    getResult(jobId: number): Observable<Result> {
        var url: string = this._scResultsUrl + '?job_id=' + jobId;
        return this.authHttp
            .get(url)
            .map(res => {
                let items: any[] = res.json()._items;
                let returnVal: Result = null;
                if (items.length == 1) {
                    let item: any = items[0];
                    returnVal = new Result(
                        jobId,
                        item.consensus_matrix_labels,
                        item.consensus_matrix_values,
                        item.consensus_matrix_file_id,
                        item.init_col_grp_file_id,
                        item.init_col_grp_feature_idx,
                        item.init_col_srt_file_id,
                        item.init_col_srt_feature_idx,
                        item.global_silhouette_score,
                        item.cluster_silhouette_scores
                    );
                } else {
                    this.logger.warn("got " + items.length + " results for " + jobId);
                }
                return returnVal;
            });
    }
}
