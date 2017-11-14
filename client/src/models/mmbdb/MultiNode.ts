import {Observable} from 'rxjs/Observable';
import {BehaviorSubject} from 'rxjs/BehaviorSubject';
import {CohortNode} from './CohortNode';
import {ComparisonNode} from './ComparisonNode';
import {CohortNodeService} from '../../services/mmbdb/CohortNodeService';
import {ComparisonNodeService} from '../../services/mmbdb/ComparisonNodeService';

import 'rxjs/add/observable/forkJoin';
import 'rxjs/add/observable/from';

// TODO refactor; see below
import {GroupedBarChartDataRecord} from '../../components/mmbdb/GroupedBarChart';

/**
 * An instance of this class represents the set of low level nodes--one
 * ComparisonNode and an array of CohortNodes--that together constitute a single
 * node in the TreeExplorer.
 */
export class MultiNode {

    /**
     * The visible children of this MultiNode. Note that the d3 tree API more
     * or less forces us to have a field called `children` used in this way.
     * (Even if we change the child accessor, it seems the layout methods still
     * store the data to a field called `children`.)
     */
    public children: MultiNode[] = null;

    /**
     * The parent of this node, or `null` for the root. This is required and
     * populated by the d3 API.
     */
    public parent: MultiNode = null;

    /**
     * The depth of this node in the tree, starting at 0 for the root. This
     * is required and populated by the d3 API.
     */
    public depth: number = null;

    /**
     * The computed x-coordinate of the node position. This is required and
     * populated by the d3 API.
     */
    public x: number = null;

    /**
     * The computed y-coordinate of the node position. This is required and
     * populated by the d3 API.
     */
    public y: number = null;

    /** The display data associated with `cohortNodes`. */
    public cohortNodesDisplayData: CohortDisplayData[] = null;

    /**
     * Constructor.
     *
     * Args:
     *     comparisonNode (ComparisonNode): The ComparisonNode for this node in
     *         the tree.
     *     cohortNodes (CohortNode[]): The CohortNodes for this node in the
     *         tree, in top-to-bottom display order.
     *     fetchedChildren (MultiNode[]): The fetched children of this node,
     *         which may or may not be displayed; see `children`.
     *     sharedData (SharedData): The data shared among all MultiNodes in
     *         a single tree.
     */
    constructor(
        public comparisonNode: ComparisonNode,
        public cohortNodes: CohortNode[],
        public fetchedChildren: MultiNode[],
        public sharedData: SharedData) {
        this.cohortNodesDisplayData = cohortNodes.map(
            (node: CohortNode) => new CohortDisplayData(null, null, null));
    }

    /**
     * Returns the computed number of interesting features (e.g., top OTUs) in
     * this MultiNode.
     *
     * Args:
     *     threshold (number): The current top-feature threshold.
     *
     * Returns:
     *     number: The number of features in this node ranked better than the
     *         threshold.
     */
    getFeatureCount(threshold: number): number {
        // TODO support features counts besides top OTUs?
        return this.comparisonNode.getNumTopOtus(threshold);
    }

    /**
     * Builds the GroupedBarChartDataRecord[] that GroupedBarChart expects.
     *
     * Args:
     *     cohortDisplayInfo (CohortDisplayInfo[]): The cohorts as they should
     *         be labeled and ordered for the GroupedBarChart.
     *     binPropertySet (BinPropertySet): The set of CohortNode properties to
     *         use when constructing the bins.
     *
     * Returns:
     *     GroupedBarChartDataRecord[]: The bar chart data ready for display.
     *
     * TODO The Great Refactoring
     */
    getDistributionData(
        cohortDisplayInfo: CohortDisplayInfo[],
        binPropertySet: BinPropertySet): GroupedBarChartDataRecord[] {

        var returnVal: GroupedBarChartDataRecord[] = [];
        returnVal.push({
            "binName": "0",
            "barDataRecords": cohortDisplayInfo.map((info: CohortDisplayInfo) => {
                return {cohort: info.label, sampleSize: <number>this.cohortNodes[info.index][binPropertySet.zeroBinAttribute]};
            })
        });
        var numBins: number = this.cohortNodes[0][binPropertySet.binHeightYAttribute].length;
        for (var i = 0; i < numBins; i++) {

            var binName: string =
                ((i == 0) ? "(" : "[") +
                (this.cohortNodes[0][binPropertySet.binStartXAttribute][i] * 100).toFixed(0) +
                "-" +
                (this.cohortNodes[0][binPropertySet.binEndXAttribute][i] * 100).toFixed(0) +
                ((i == numBins-1) ? "]" : ")");

            returnVal.push({
                "binName": binName,
                "barDataRecords": cohortDisplayInfo.map((info: CohortDisplayInfo) => {
                    return {cohort: info.label, sampleSize: <number>this.cohortNodes[info.index][binPropertySet.binHeightYAttribute][i]};
                })
            });
        }
        return returnVal;
    }

    /**
     * Shows the children of this node, fetching them from the API if necessary.
     *
     * Args:
     *     resendRoot (boolean): Whether to re-publish the root node to the
     *         stream returned by `getRootMultiNode`, so that observers will
     *         be notified of the change.
     */
    showChildren(resendRoot: boolean): void {
        // fetch children--note we won't actually call the server if the
        // children were previously fetched
        var stream: Observable<number> = MultiNode.fetchChildren([this]);
        stream.subscribe(
            (count: number) => {
                if (count !== null) {
                    this.children = this.fetchedChildren;
                    if (resendRoot) {
                        this.sharedData.resendRoot();
                    }
                }
            },
            (err) => this.sharedData.rootStream.error(err)
        );
    }

    /**
     * Given an array of MultiNodes, fetches their children.
     *
     * Args:
     *     parents (MultiNode[]): The nodes whose children are to be fetched.
     *
     * Returns:
     *     Observable<number>: A stream that will publish `null` immediately,
     *         followed later by a single number which will be the number
     *         of children fetched (not counting any lost to pruning).
     */
    static fetchChildren(parents: MultiNode[]): Observable<number> {
        var nodes: MultiNode[] = MultiNode.filterParents(parents);
        if (nodes.length == 0) {
            return Observable.from([null, 0]);
        }
        var stream: BehaviorSubject<number> = new BehaviorSubject<number>(null);
        var total: number = 0;
        var sharedData: SharedData = nodes[0].sharedData;
        // create calls to fetch the ComparisonNode/CohortNodes and join
        // their streams
        var comparisonNodeStream: Observable<ComparisonNode[]> =
            sharedData.comparisonNodeService.getChildren(
                nodes.map((node) => node.comparisonNode));
        var cohortNodeStream: Observable<CohortNode[]> =
            sharedData.cohortNodeService.getChildren(
                [].concat.apply([], nodes.map((node) => node.cohortNodes)));
        var joinedNodeStream: Observable<any[]> = Observable.forkJoin(
            comparisonNodeStream, cohortNodeStream);
        // when the API returns the items, assemble them into MultiNodes
        joinedNodeStream.subscribe(
            (nodeArray: any[]) => {
                // first array will be comparison nodes, second array will
                // be cohort nodes
                var comparisonNodes: ComparisonNode[] = nodeArray[0];
                var cohortNodes: CohortNode[] = nodeArray[1];
                // build children
                nodes.forEach((node) => {
                    node.buildChildren(comparisonNodes, cohortNodes);
                    total += node.fetchedChildren.length;
                });
                stream.next(total);
            },
            (err) => sharedData.rootStream.error(err)
        );
        return stream;
    }

    /**
     * Given an array of MultiNodes, returns those members whose children
     * aren't yet fetched.
     *
     * Args:
     *     parents (MultiNode[]): The nodes whose children are to be examined.
     *
     * Returns:
     *     MultiNode[]: The members of `parents` whose children aren't yet
     *         fetched.
     */
    static filterParents(parents: MultiNode[]) {
        var returnVal: MultiNode[] = [];
        if (parents !== null) {
            returnVal = parents.filter((node) => node.fetchedChildren === null);
        }
        return returnVal;
    }

    /**
     * Hides the children of this node.
     *
     * Args:
     *     resendRoot (boolean): Whether to re-publish the root node to the
     *         stream returned by `getRootMultiNode`, so that observers will
     *         be notified of the change.
     */
    hideChildren(resendRoot: boolean): void {
        this.children = null;
        if (resendRoot) {
            this.sharedData.resendRoot();
        }
    }

    /**
     * Given sets of raw ComparisonNodes and CohortNodes needed to build
     * the child MultiNodes of this MultiNode, assembles the correct raw nodes
     * into child MultiNodes, prunes empty branches, and stores those that
     * remain as `fetchedChildren`.
     *
     * Args:
     *     comparisonCandidates (ComparisonNode[]): A set (or superset) of the
     *         raw ComparisonNode objects required to build the child MultiNodes
     *         of this MultiNode.
     *     cohortCandidates (CohortNode[]): A set (or superset) of the raw
     *         CohortNode objects required to build the child MultiNodes of
     *         this MultiNode.
     */
    buildChildren(
        comparisonCandidates: ComparisonNode[],
        cohortCandidates: CohortNode[]): void {

        // array of the ComparisonNode objects we actually need, one per child
        var childComparisonNodes: ComparisonNode[] = [];
        // 2D array of the CohortNode objects we actually need; first dimension
        // is one per child, and second dimension is per cohort
        var childCohortNodes: CohortNode[][] = [];

        // find the candidate ComparisonNodes that refer to our ComparisonNode
        // and sort them by name (later, we'll sort the CohortNodes to match)
        comparisonCandidates.forEach((candidate) => {
            if (candidate.parentNodeIdx == this.comparisonNode.nodeIdx) {
                childComparisonNodes.push(candidate);
            }
        });
        childComparisonNodes.sort((node1, node2) => node1.name.localeCompare(node2.name));

        // find the candidate CohortNodes that match the ComparisonNodes
        // first, group the candidate CohortNodes by cohortId
        var groupedCohortCandidates: any = d3.nest()
            .key((d: CohortNode) => d.cohortId).entries(cohortCandidates);
        // now, in the same cohort order as our cohortNodes, build arrays of children
        this.cohortNodes.forEach((ourCohortNode) => {

            // get all of the candidate child CohortNodes matching this cohortId
            var cohortId: string = ourCohortNode.cohortId;
            var ourCohortChildren: CohortNode[] = [];
            var candidates: CohortNode[] = groupedCohortCandidates.filter(
                (group: any) => group.key == cohortId)[0].values;

            // from the candidate child CohortNodes matching this cohortId, grab
            // those that are actually children of the current CohortNode
            candidates.forEach((candidate) => {
                if (candidate.parentNodeIdx == ourCohortNode.nodeIdx) {
                    ourCohortChildren.push(candidate);
                }
            });
            // sort them to match the ComparisonNodes and record them for the
            // next step
            ourCohortChildren.sort(
                (node1, node2) => node1.name.localeCompare(node2.name));
            childCohortNodes.push(ourCohortChildren);
        });

        // assemble the child MultiNodes
        this.fetchedChildren = [];
        for (var i: number = 0; i < childComparisonNodes.length; i++) {
            this.fetchedChildren.push(new MultiNode(
                childComparisonNodes[i],
                childCohortNodes.map((cohortNodes) => cohortNodes[i]),
                null,
                this.sharedData
            ));
        }

        // prune: discard any children with zero abundance in all cohorts
        this.fetchedChildren = this.fetchedChildren.filter((child) => {
            // if there's some abundance > 0 among the cohorts, keep it
            var sum: number =  d3.sum(child.cohortNodes, (node) => {
                // check the last quantile
                var quantiles: number[] = node.relativeAbundanceQuantiles;
                return quantiles[quantiles.length-1];
            });
            return sum > 0;
        });
    }

    /**
     * Returns a stream that publishes the root MultiNode for a tree.
     *
     * Args:
     *     comparisonId (string): The comparison_id to use when loading
     *         ComparisonNodes.
     *     cohortIds (string[]): The cohort_id values to use when loading
     *         ComparisonNodes, ordered as they should appear on screen top to
     *         bottom.
     *     fetchedChildLevels (number): The number of tree levels beneath the
     *         root to fetch immediately.
     *     comparisonNodeService (ComparisonNodeService): ComparisonNodeService
     *         singleton provided by ng2 DI.
     *     cohortNodeService (CohortNodeService): CohortNodeService singleton
     *         provided by ng2 DI.
     *
     * Returns:
     *     Observable<MultiNode> that publishes the root MultiNode.
     */
    static getRootMultiNode(
        comparisonId: string,
        cohortIds: string[],
        fetchedChildLevels: number=0,
        comparisonNodeService: ComparisonNodeService,
        cohortNodeService: CohortNodeService): Observable<MultiNode> {

        // create an object to store the data common to MultiNodes in the tree
        var sharedData: SharedData = new SharedData(
            comparisonNodeService,
            cohortNodeService,
            new BehaviorSubject<MultiNode>(null)
        );

        // get the comparison and cohort nodes for the levels we need
        var comparisonNodeStream: Observable<ComparisonNode[]> =
            comparisonNodeService.getNodesForLevels(
                comparisonId,
                MultiNode.getLevelNames().slice(0, fetchedChildLevels+1));
        var cohortNodeStream: Observable<CohortNode[]> =
            cohortNodeService.getNodesForLevels(
                cohortIds,
                MultiNode.getLevelNames().slice(0, fetchedChildLevels+1));
        var joinedNodeStream: Observable<any[]> = Observable.forkJoin(
            comparisonNodeStream, cohortNodeStream);
        // process all the nodes
        joinedNodeStream.subscribe(
            (nodeArray: any[]) => {
                // first array will be comparison nodes, second array will be
                // cohort nodes
                var comparisonNodes: ComparisonNode[] = nodeArray[0];
                var cohortNodes: CohortNode[] = nodeArray[1];
                // there'll be only one root comparison node; grab it
                var rootComparisonNode: ComparisonNode = comparisonNodes
                    .filter((d: ComparisonNode) => d.level == "root")[0];
                // there'll be one root cohort node per element in cohortIds;
                // grab them
                var rootCohortNodes: CohortNode[] = [];
                cohortIds.forEach((id) => {
                    rootCohortNodes.push(
                        cohortNodes.filter(
                            (d: CohortNode) =>
                                d.level == "root" && d.cohortId == id
                        )[0]
                    );
                });
                // now assemble the MultiNode
                var root: MultiNode = new MultiNode(
                    rootComparisonNode,
                    rootCohortNodes,
                    null,
                    sharedData);
                // build children
                var currentLevel: MultiNode[] = [root];
                for (var i: number = 0; i < fetchedChildLevels; i++) {
                    // get all children for everything in currentLevel
                    currentLevel.forEach((node) =>
                        node.buildChildren(comparisonNodes, cohortNodes));
                    // reset currentLevel to all the children we just added
                    currentLevel = currentLevel
                        .map((node: MultiNode) => node.fetchedChildren)
                        .reduce((previous: MultiNode[], current: MultiNode[]) =>
                            previous.concat(current), []);
                }
                sharedData.rootStream.next(root);
            },
            (err) => sharedData.rootStream.error(err)
        );
        return sharedData.rootStream;
    }

    /**
     * Releases root stream resources.
     */
    releaseRootStream(): void {
        this.sharedData.rootStream.unsubscribe();
    }

    /**
     * Returns the names of the levels in the tree.
     */
    static getLevelNames(): string[] {
        return ["root", "kingdom", "phylum", "class", "order", "family", "genus", "species", "otu_name"];
    }
}

/**
 * An instance of this class represents a parent-child link between two
 * MultiNodes. Instances will be generated by the d3 API.
 */
export class MultiLink {

    /** The parent node. It must be called `source` for d3. */
    public source: MultiNode = null;

    /** The child node. It must be called `target` for d3. */
    public target: MultiNode = null;
}

/**
 * An instance of this class represents the display data associated with a
 * single cohort in a single MultiNode.
 */
export class CohortDisplayData {

    /**
     * Constructor.
     *
     * Args:
     *     y (number): The starting y-coordinate of the rectangle.
     *     height (number): The height in pixels of the rectangle.
     *     linkPath (string): The SVG path definition for a curve connecting
     *         this rectangle to its parent rectangle.
     */
    constructor(
        public y: number,
        public height: number,
        public linkPath: string) {
    }
}

/**
 * This is an inner class used to encapsulate data shared among all MultiNode
 * objects in a tree.
 */
class SharedData {

    /**
     * Constructor.
     *
     * Args:
     *     comparisonNodeService (ComparisonNodeService): Instance from DI.
     *     cohortNodeService (CohortNodeService): Instance from DI.
     *     rootStream (BehaviorSubject<MultiNode>): The stream returned by
     *         `getRootMultiNode` for this tree.
     */
    constructor(
        public comparisonNodeService: ComparisonNodeService,
        public cohortNodeService: CohortNodeService,
        public rootStream: BehaviorSubject<MultiNode>
    ) {
    }

    /**
     * Publishes the root MultiNode for this tree again, notifying subscribers
     * of an update.
     */
    resendRoot(): void {
        this.rootStream.next(this.rootStream.getValue());
    }
}

/**
 * An array of CohortDisplayInfo objects is used to extract data for display in
 * the GroupedBarChart. The elements in the array should be in the order they're
 * to be displayed in the GroupedBarChart, which may differ from the order
 * they're stored in this MultiNode. The `index` field on each CohortDisplayInfo
 * object specifies the index of the cohort in this MultiNode, so they can be
 * looked up and rearranged.
 * TODO The Great Refactoring
 */
export class CohortDisplayInfo {
    constructor(
        public label: string,
        public index: number) {
    }
}

/**
 * This class represents a set of CohortNode properties used to build a
 * GroupedBarChart.
 * TODO The Great Refactoring
 */
export class BinPropertySet {
    constructor(
        public zeroBinAttribute: string,
        public binStartXAttribute: string,
        public binEndXAttribute: string,
        public binHeightYAttribute: string) {
    }
}

/**
 * This is the set of CohortNode properties used to build a GroupedBarChart of
 * relative abundances.
 * TODO more of these, and relocate, etc.
 */
export var RELATIVE_ABUNDANCE_BIN_PROPERTY_SET: BinPropertySet = new BinPropertySet(
    'relativeAbundanceHistoNumZeros',
    'relativeAbundanceHistoBinStartX',
    'relativeAbundanceHistoBinEndX',
    'relativeAbundanceHistoBinHeightY'
);
