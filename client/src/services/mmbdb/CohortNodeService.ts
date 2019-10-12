import {Injectable} from '@angular/core';
import {AuthHttp} from 'angular2-jwt';
import {Observable} from 'rxjs/Observable';
import {CohortNode} from '../../models/mmbdb/CohortNode';
import {EveUtilities} from '../common/EveUtilities';

import 'rxjs/add/observable/forkJoin';
import 'rxjs/add/observable/of';
/**
 * This class provides methods for working with the cohort_phylo_tree_nodes
 * endpoint.
 */
@Injectable()
export class CohortNodeService {

    private cohortTreeUrl: string = "/api/v2/cohort_phylo_tree_nodes";

    constructor(private authHttp: AuthHttp) {
    }

    /**
     * Given a URL that returns multiple CohortNode items, streams all of
     * the returned items, even if paginated.
     *
     * Args:
     *     url (string): The query URL.
     *
     * Returns:
     *      Observable<CohortNode[]> that'll publish a single array
     *      containing all of the matching nodes.
     */
    getPagedItems(url: string): Observable<CohortNode[]> {
        return EveUtilities.getAllItems(url, this.authHttp).map((nodes: any[]) => {
            return nodes.map((node: any) => new CohortNode(
                node._id,
                node.node_name,
                node.node_level,
                node.cohort_id,
                node.node_idx,
                node.parent_node_idx,
                node.relative_abundance_mean,
                node.relative_abundance_quantiles,
                node.relative_abundance_histo_num_zeros,
                node.relative_abundance_histo_bin_start_x,
                node.relative_abundance_histo_bin_end_x,
                node.relative_abundance_histo_bin_height_y,
                node.num_unique_otus_mean,
                node.num_unique_otus_density_plot_x,
                node.num_unique_otus_density_plot_y,
                node.num_unique_otus_histo_num_zeros,
                node.num_unique_otus_histo_bin_start_x,
                node.num_unique_otus_histo_bin_end_x,
                node.num_unique_otus_histo_bin_height_y,
                node.normalized_entropy_mean,
                node.normalized_entropy_histo_num_zeros,
                node.normalized_entropy_histo_bin_start_x,
                node.normalized_entropy_histo_bin_end_x,
                node.normalized_entropy_histo_bin_height_y
            ));
        });
    }

    /**
     * Returns the CohortNodes for a specified array of cohorts and array of
     * taxonomy levels.
     *
     * Args:
     *     cohortIds (string[]): An array of cohort_id values to match.
     *     levels (string[]): An array of node_level values to match.
     *
     * Returns:
     *      Observable<CohortNode[]> that'll publish a single array
     *      containing all of the matching nodes.
     */
    getNodesForLevels(cohortIds: number[], levels: string[]): Observable<CohortNode[]> {
        var url: string = this.cohortTreeUrl + '?' +
            'cohort_id=' + cohortIds.join(',') +
            '&node_level=' + levels.join(',')
        return this.getPagedItems(url);
    }

    /**
     * Given an array of CohortNodes, returns all of their children.
     *
     * Args:
     *     parent (CohortNode[]): The parent nodes.
     *
     * Returns:
     *      Observable<CohortNode[]> that'll publish a single array
     *      containing all of the child nodes.
     */
    getChildren(parents: CohortNode[]): Observable<CohortNode[][]> {
        var parentIdxs = new Set()
        for (var i = 0; i < parents.length; i++){
            parentIdxs.add(parents[i].nodeIdx);
        }
        //var allChildren: Observable<Array<CohortNode>> = Observable.of(new Array<CohortNode>())
        var allChildrenObs: Array<Observable<CohortNode[]>> = new Array<Observable<CohortNode[]>>();
        var baseUrl = this.cohortTreeUrl;
        parentIdxs.forEach((parentNodeIdx) => {
            var cohorts : CohortNode[] = parents.filter((parent) => parent.nodeIdx == parentNodeIdx);
            var cohortIds : Number[] = cohorts.map((cohort) => cohort.cohortId)
            var url: string =  baseUrl + '?cohort_id=' + cohortIds.join(',') +
                '&parent_node_idx=' + parentNodeIdx + '&max_results=1000';
            var children : Observable<CohortNode[]> = this.getPagedItems(url);
            allChildrenObs.push(children)
        });
        var allChildren: Observable<CohortNode[][]> = Observable.forkJoin(allChildrenObs);
        return allChildren;
    }

}
