import {Injectable} from '@angular/core';
import {Response} from '@angular/http';
import {AuthHttp} from 'angular2-jwt';
import {Observable} from 'rxjs/Observable';
import {Cohort, Comparison, CohortPhylumData} from '../../models/mmbdb/CohortComparison';

@Injectable()
export class CohortComparisonService {
    
    private comparisonUrl: string = '/api/v2/cohort_comparisons';
    
    private cohortUrl: string = '/api/v2/cohorts';
    
    private cohortPhylumTreeUrl: string = '/api/v2/cohort_phylo_tree_nodes'
    
    constructor(public authHttp: AuthHttp) {
    }
    
    /**
     * Read a single cohort
     */
    getSingleCohort(cohortId: number): Observable<Cohort> {
        var endpoint = this.cohortUrl + '/' + cohortId;
        return this.authHttp
            .get(endpoint)
            .map(response => <Cohort> response.json());
    }
    
    /**
     * Read all cohorts
     */
    getCohorts(): Observable<Cohort[]> {
        return this.authHttp
            .get(this.cohortUrl)
            .map(response => <Cohort[]>response.json()._items);
    }
    
     /**
     * Read a single comparison
     */
    getComparison(comparisonId: number): Observable<Comparison> {
        var endpoint = this.comparisonUrl + '/' + comparisonId;
        return this.authHttp
            .get(endpoint)
            .map(response => <Comparison> response.json());
    }
    
    /**
     * Read all comparisons
     */
    getComparisons(): Observable<Comparison[]> {
        // when fetching the whole list, we only need display_name and _id.
        // some of the other fields are big. skip them for now.
        // later, when fetching a single comparison the user has selected from
        // this list, we'll grab the big fields.
        var projectionUrl = this.comparisonUrl + "?fields=display_name";
        return this.authHttp
            .get(projectionUrl)
            .map(response => <Comparison[]>response.json()._items);
    }
    
    /**
     * Read multiple cohorts in batch
     * @param: cohortIDs array of cohort ids
     */ 
    getAllComparingCohorts(cohortIDs: Array<number>) {
        let observableBatch: any = [];
        for (var i = 0; i < cohortIDs.length; i++) {
            observableBatch.push(this.authHttp.get(this.cohortUrl + "/" + cohortIDs[i]).map(response => <Cohort> response.json()));
        }
        return Observable.forkJoin(observableBatch);
    }
    
    //TODO: need to insert line break in those long cohort names
    getAllComparingCohortsNew(cohortIDs: Array<number>) {
        let observableBatch: any = [];
        for (var i = 0; i < cohortIDs.length; i++) {
            observableBatch.push(this.authHttp.get(this.cohortUrl + "/" + cohortIDs[i]).map(response => {
                var json = response.json();
                var display_name_long_new = json.display_name_long;
                if (json.display_name_long.indexOf(",") != -1) {
                    display_name_long_new = json.display_name_long.substring(0, json.display_name_long.indexOf(",") + 1);
                    display_name_long_new = display_name_long_new.concat("<br>");
                    display_name_long_new = display_name_long_new.concat(json.display_name_long.substring(json.display_name_long.indexOf(",") + 1));
                }
                return new Cohort(json._id,
                    json.display_name_short,
                    display_name_long_new,
                    json.num_samples);
            }));
        }
        return Observable.forkJoin(observableBatch);
    }
    
    /**
     * Read multiple cohort phylum tree data (including abundance represented by relative_abundance_*, richness represented by num_top_otu_*) in batch
     * @param: cohortIDs array of cohort ids
     */ 
    getAllComparingCohortPhylumTreeData(cohortIDs: Array<number>) {
        let observableBatch: any = [];
        for (var i = 0; i < cohortIDs.length; i++) {
            observableBatch.push(this.authHttp.get(this.cohortPhylumTreeUrl + "?cohort_id=" + cohortIDs[i] + "&node_level=phylum&sort=node_name")
                .map(response => <CohortPhylumData[]> response.json()._items));
        }
        return Observable.forkJoin(observableBatch);
    }
    
    /**
     * Read multiple cohort root data (mainly to get overall richness data) in batch
     * @param: cohortIDs array of cohort ids
     */ 
    getAllComparingCohortsRootData(cohortIDs: Array<number>) {
        let observableBatch: any = [];
        for (var i = 0; i < cohortIDs.length; i++) {
            observableBatch.push(this.authHttp.get(this.cohortPhylumTreeUrl + "?cohort_id=" + cohortIDs[i] + "&node_level=root")
                .map(response => <CohortPhylumData[]> response.json()._items));
        }
        return Observable.forkJoin(observableBatch);
    }
}
