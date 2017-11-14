import {Injectable} from '@angular/core';
import {AuthHttp} from 'angular2-jwt';
import {Observable} from 'rxjs/Observable';

import {Result, TopGenes, Sample, PhenotypeData} from '../../models/knoweng/results/SampleClustering';
import {EveUtilities} from '../common/EveUtilities';
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
                        new TopGenes(item.top_genes),
                        item.samples.map((sample: any) => new Sample(sample.id, sample.cluster)),
                        item.genes_heatmap,
                        item.samples_heatmap,
                        item.phenotypes.map((pheno: any) => new PhenotypeData(pheno.name, pheno.score, pheno.values)));
                } else {
                    this.logger.warn("got " + items.length + " results for " + jobId);
                }
                return returnVal;
            });
    }
}
