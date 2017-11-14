import {Injectable} from '@angular/core';
import {AuthHttp} from 'angular2-jwt';
import {Observable} from 'rxjs/Observable';

import {ComparisonGeneSet, UserGeneSet, ComparisonGeneSetScores, Result} from '../../models/knoweng/results/GeneSetCharacterization';
import {EveUtilities} from '../common/EveUtilities';
import {LogService} from '../common/LogService';

@Injectable()
export class GeneSetCharacterizationService {

    private _publicGeneSetsUrl: string = '/api/v2/public_gene_sets';
    private _gscResultsUrl: string = '/api/v2/gene_set_characterizations';

    constructor(private authHttp: AuthHttp, private logger: LogService) {
    }

    /**
     * Returns the ComparisonGeneSets for a specified array of set_ids.
     *
     * Args:
     *     setIds (string[]): An array of set_id values to match.
     *
     * Returns:
     *      Observable<ComparisonGeneSet[]> that'll publish a single array
     *      containing all of the matching ComparisonGeneSets.
     */
    getComparisonGeneSets(setIds: string[], speciesId: string): Observable<ComparisonGeneSet[]> {
        return this.getComparisonGeneSetsChunks(setIds, speciesId, 50).toArray();
    }

    getComparisonGeneSetsChunks(setIds: string[], speciesId: string, chunkSize: number, chunkIndex = 0): Observable<ComparisonGeneSet> {
        let sliceStart: number = chunkIndex * chunkSize;
        let sliceEnd: number = sliceStart + chunkSize;
        let nextChunkIndex: number = chunkIndex + 1;
        if (sliceEnd >= setIds.length) {
            sliceEnd = setIds.length;
            nextChunkIndex = null;
        }
        let setIdsChunk: string[] = setIds.slice(sliceStart, sliceEnd);
        let url: string = this._publicGeneSetsUrl +
            '?species_id=' + speciesId + '&set_id=' + setIdsChunk.join() ;
        setIdsChunk = undefined;    
        return EveUtilities
            .getAllItems(url, this.authHttp)
            .flatMap((cgsData: any[]) => {
                let itemStream: Observable<ComparisonGeneSet> = Observable.from(cgsData.map((item: any) => new ComparisonGeneSet(
                    item.set_id,
                    item.set_name,
                    item.species_id,
                    item.gene_count,
                    item.url,
                    item.collection,
                    item.edge_type_name,
                    item.supercollection
                )));
                if (nextChunkIndex !== null) {
                    itemStream = itemStream.concat(this.getComparisonGeneSetsChunks(setIds, speciesId, chunkSize, nextChunkIndex));
                }
                return itemStream;
        });
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
        var url: string = this._gscResultsUrl + '?job_id=' + jobId;
        return this.authHttp
            .get(url)
            .map(res => {
                let items: any[] = res.json()._items;
                let returnVal: Result = null;
                if (items.length == 1) {
                    let item: any = items[0];
                    let userGeneSets: UserGeneSet[] = item.user_gene_sets.map((ugs: any) => {
                        return new UserGeneSet(ugs.set_id, ugs.gene_ids);
                    });
                    let setLevelScores: ComparisonGeneSetScores =
                        new ComparisonGeneSetScores(item.set_level_scores);
                    returnVal = new Result(jobId, userGeneSets, setLevelScores, item.minimum_score);
                } else {
                    this.logger.warn("got " + items.length + " results for " + jobId);
                }
                return returnVal;
            });
    }
}
