import {Injectable} from '@angular/core';
import {AuthHttp} from 'angular2-jwt';
import {Observable} from 'rxjs/Observable';
import {CohortNode} from '../../models/mmbdb/CohortNode';
import {EveUtilities} from '../common/EveUtilities';

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
    getNodesForLevels(cohortIds: string[], levels: string[]): Observable<CohortNode[]> {
        var url: string = this.cohortTreeUrl + '?' + 
			cohortIds.map((cohortId) => 'cohort_id=' + cohortId + '&').join() +
			levels.map((level) => 'level=' + level + '&').join()
		//remove trailing '&'
		url = url.substring(0, url.length-1)
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
    getChildren(parents: CohortNode[]): Observable<CohortNode[]> {
        var orTerms: String[] = parents.map((parent) => '{"cohort_id" : "' + parent.cohortId + '", "parent_node_idx": ' + parent.nodeIdx + '}');
        var url: string = this.cohortTreeUrl + '?where={"$or": [' + orTerms.join() + ']}';
        return this.getPagedItems(url);
    }
}
