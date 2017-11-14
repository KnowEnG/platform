/// <reference path="../../typings/d3/d3.d.ts" />
import {Component, Input, OnChanges, SimpleChange} from '@angular/core';
import {Comparison} from '../../models/mmbdb/CohortComparison';
import {CohortNode} from '../../models/mmbdb/CohortNode';
import {MultiNode, MultiLink, CohortDisplayData} from '../../models/mmbdb/MultiNode';
import {CohortNodeService} from '../../services/mmbdb/CohortNodeService';
import {ComparisonNodeService} from '../../services/mmbdb/ComparisonNodeService';
import {TreeDetailTable} from './TreeDetailTable';

// note: this component requires d3.js

@Component ({
    moduleId: module.id,
    selector: 'tree-explorer',
    styleUrls: ['./TreeExplorer.css'],
    templateUrl: './TreeExplorer.html'
})

export class TreeExplorer implements OnChanges {
    class = 'relative';

    /**
     * The Comparison object representing the current comparison.
     */
    @Input()
    comparison: Comparison;

    /**
     * Number of top OTUs to show.
     */
    @Input()
    topOtuThreshold: number;

    /** Pixels between top edge of SVG and beginning of SVG content. */
    marginTop: number = 47;
    /** Pixels between right edge of SVG and beginning of SVG content. */
    marginRight: number = 1;
    /** Pixels between bottom edge of SVG and beginning of SVG content. */
    marginBottom: number = 16;
    /** Pixels between left edge of SVG and beginning of SVG content. */
    marginLeft: number = 54;
    /** Width of content area of SVG. */
    width: number = 1580 - this.marginLeft - this.marginRight;
    /**
     * Minimum height of content area of SVG; actual height will exceed this
     * number if the tree layout requires more vertical space.
     */
    minHeight: number = 1000;
    /** Current height of content area of SVG. */
    currentHeight: number = this.minHeight;

    /** Width of rectangles at each node. */
    nodeWidth: number = 29;
    /** Horizontal pixels between center of each level of tree. */
    horizontalSpacing: number = 261;

    /** Names of the tree levels to appear across top of SVG. */
    levelNames: string[];

    /** MultiNode object representing the root of the tree. */
    root: MultiNode;
    /** MultiNodes currently shown on screen. */
    shownNodes: MultiNode[];
    /** Links currently shown on screen. */
    shownLinks: MultiLink[];

    /** d3 tree layout. */
    tree: any;
    /** Number of tree levels to expand before any user interaction. */
    numInitialLevelsExpanded: number = 2;
    /** Number of top tree levels to hide. */
    numTopHiddenLevels: number = 1; // don't show root
    /** Number of bottom tree levels to hide. */
    numBottomHiddenLevels: number = 2; // don't show species or OTU

    /** MultiNode whose children are displayed in the table. */
    nodeForTable: MultiNode = null;

    /**
     * Number by which to multiply relative abundance values to arrive at
     * rectangle heights in pixels.
     */
    abundanceScaleFactor: number = 200;

    /** Minimum number of vertical pixels between nodes in the same level. */
    minYSpacing: number = 10;

    /** Whether the SVG is still initializing. */
    initializing: boolean = true;

    /**
     * Constructor. Populates `levelNames` and creates `tree`.
     *
     * Args:
     *     _cohortNodeService (CohortNodeService): CohortNodeService singleton
     *         from ng2 DI.
     *     _comparisonNodeService (ComparisonNodeService): ComparisonNodeService
     *         singleton from ng2 DI.
     */
    constructor(
        public _cohortNodeService: CohortNodeService,
        public _comparisonNodeService: ComparisonNodeService) {

        this.levelNames = MultiNode.getLevelNames();
        this.levelNames = this.levelNames.slice(
            this.numTopHiddenLevels,
            this.levelNames.length - this.numBottomHiddenLevels);

        this.tree = d3.layout.tree().size([this.minHeight, this.width]);
    }
    /** Handles updates to the inputs. */
    ngOnChanges(changes: {[propertyName: string]: SimpleChange}) {
        // we need to reload the root if comparison changed
        var reload: boolean = false;
        for (let propName in changes) {
            if (propName == 'comparison') {
                reload = true;
                break;
            }
        }
        if (reload) {
            this.initializing = true;
            this.loadRoot();
        } else {
            this.update(this.root);
        }
    }
    /**
     * Fetches `root` and calls `update()` when `root` is ready.
     */
    loadRoot() {
        if (this.root) {
            this.root.releaseRootStream();
        }
        // we need the cohort ids in the order they'll be displayed, top to
        // bottom, which for MMBDB is variant then baseline then individual
        var cohortIds: string[] = [
            this.comparison.variant_cohort_id,
            this.comparison.baseline_cohort_id];
        if (this.comparison.patient_cohort_id) {
            cohortIds.push(this.comparison.patient_cohort_id);
        }
        MultiNode.getRootMultiNode(
            this.comparison._id,
            cohortIds,
            this.numInitialLevelsExpanded,
            this._comparisonNodeService,
            this._cohortNodeService)
            .subscribe((root: MultiNode) => this.update(root));
    }
    /**
     * Updates the tree layout after a change to the MultiNodes.
     *
     * Args:
     *     root (MultiNode): The root MultiNode, possibly different from
     *         the current `this.root`.
     */
    update(root: MultiNode): void {
        // service will immediately publish null, so check for that
        if (root !== null) {
            this.root = root;
            // if we're initializing, automatically expand levels according to
            // numInitialLevelsExpanded
            // if we're not initializing, don't do that; the user may have
            // intentionally collapsed some of the levels that were
            // automatically opened
            if (this.initializing) {
                this.showInitialLevelsExpanded();
                this.initializing = false;
            }

            // use d3.tree to compute rough positions of the nodes
            this.shownNodes = this.tree.nodes(this.root);
            // generate a list of the links from the list of nodes
            this.shownLinks = this.tree.links(this.shownNodes);

            this.pruneHiddenLevels();

            this.prepareNodesForDisplay();
            this.prepareLinksForDisplay();
        }
    }
    /**
     * Expands tree during initialization to show `numInitialLevelsExpanded`.
     */
    showInitialLevelsExpanded(): void {
        var levelNodes: MultiNode[] = [this.root];
        for (var i: number = 0; i < this.numInitialLevelsExpanded; i++) {
            var nextLevelNodes: MultiNode[] = [];
            levelNodes.forEach((node: MultiNode) => {
                node.showChildren(false);
                Array.prototype.push.apply(nextLevelNodes, node.children);
            });
            levelNodes = nextLevelNodes;
        }
    }
    /**
     * Removes nodes and links from hidden levels.
     */
    pruneHiddenLevels(): void {
        var minDepth: number = this.numTopHiddenLevels;
        var maxDepth: number = this.levelNames.length + this.numTopHiddenLevels;
        this.shownNodes = this.shownNodes.filter((node: MultiNode) => {
            return node.depth >= minDepth && node.depth <= maxDepth;
        });
        this.shownLinks = this.shownLinks.filter((link: MultiLink) => {
            return link.source.depth >= minDepth && link.source.depth <= maxDepth;
        });
    }
    /**
     * Prepares nodes and their associated cohort rectangles for display.
     */
    prepareNodesForDisplay(): void {
        this.shownNodes.forEach((node: MultiNode) => {
            // switch vertical layout (d3 default) to horizontal
            this.switchXY(node);
            // enforce fixed width per level
            node.x = this.getXForDepth(node.depth);
            // calculate blocks (rectangles) for cohorts
            this.calculateCohortBlocks(node);
        });
        // now go level by level and correct rectangle collisions
        var nodesByLevel: any = d3.nest()
            .key((node: MultiNode) => node.depth.toString())
            .sortKeys(d3.descending)
            .sortValues((a: MultiNode, b: MultiNode) => d3.ascending(a.y, b.y))
            .entries(this.shownNodes);
        this.currentHeight = this.minHeight;
        nodesByLevel.forEach((d: any) => {
            // outer loop: one level of the tree
            // inner loop: MultiNodes in the level, sorted from top of screen
            // to bottom
            var lastY: number = 0;
            d.values.forEach((node: MultiNode) => {
                var minY: number = lastY + this.minYSpacing;
                var thisY: number = node.y + node.cohortNodesDisplayData[0].y;
                var adjustment: number = minY - thisY;
                if (adjustment > 0) {
                    node.y += adjustment;
                }
                var lastCohortNodeDisplayData: any =
                    node.cohortNodesDisplayData[
                        node.cohortNodesDisplayData.length-1];
                lastY = node.y + lastCohortNodeDisplayData.y +
                    lastCohortNodeDisplayData.height;
            });
            this.currentHeight = Math.max(this.currentHeight, lastY);
        });
    }
    /**
     * Prepares links for display.
     */
    prepareLinksForDisplay(): void {
        // first, group the links according to the source node
        var groupedLinks: any = d3.nest()
            .key((link: MultiLink) => link.source.comparisonNode.id)
            .entries(this.shownLinks);
        // now process them in batches, one batch per source node
        groupedLinks.forEach((d: any) => {
            this.calculateLinkPathsForSource(d.values);
        });
    }
    /**
     * Switches the x- any y-coordinates of a MultiNode, converting from the
     * default layout with the root at the top to a layout with the root on
     * the left.
     *
     * Args:
     *     node (MultiNode): The node whose x- and y-coordinates should be
     *         switched.
     */
    switchXY(node: MultiNode): void {
        var origX = node.x;
        var origY = node.y;
        node.y = origX;
        node.x = origY;
    }
    /**
     * Returns the x-coordinate for a given depth in the tree.
     *
     * Args:
     *     depth (number): The depth in the tree, where 0 represents the root,
     *         1 represents the children of the root, and so on.
     *
     * Returns:
     *     number: x-coordinate for the depth.
     */
    getXForDepth(depth: number): number {
        return (depth-this.numTopHiddenLevels) * this.horizontalSpacing;
    }
    /**
     * Given a MultiNode, calculates the starting y-coordinate and height of
     * each cohort rectangle associated with the node.
     *
     * Args:
     *     node (MultiNode): The node to process.
     */
    calculateCohortBlocks(node: MultiNode): void {
        // lastY tracks the position where the previous block was drawn
        // initialize it so that the all of the rectangles for this multinode
        // will be centered about the node's group's position
        var lastY: number = -0.5 * this.abundanceScaleFactor * d3.sum(
            node.cohortNodes,
            (cNode: CohortNode) => cNode.relativeAbundanceMean);
        for (var i: number = 0; i < node.cohortNodes.length; i++) {
            node.cohortNodesDisplayData[i].y = lastY;
            var scaledAbundance: number =
                node.cohortNodes[i].relativeAbundanceMean *
                this.abundanceScaleFactor;
            node.cohortNodesDisplayData[i].height = scaledAbundance;
            lastY += scaledAbundance;
        }
    }
    /**
     * Given all the links associated with a single source, computes their SVG
     * paths.
     *
     * Args:
     *     links (MultiLink[]): The links to process.
     */
    calculateLinkPathsForSource(links: MultiLink[]): void {
        var curvature: number = .5;

        // sort the links from the top of the screen to the bottom of the screen
        links.sort((a: any, b: any) => d3.ascending(a.y, b.y));

        // all links in the array will have the same source MultiNode
        var source: any = links[0].source;
        var sourceCohortsDisplayData: CohortDisplayData[] =
            source.cohortNodesDisplayData;

        // all links in the array will have the same starting x coordinate
        var x0: number = source.x + this.nodeWidth/2;

        // iterate over cohorts then over links
        for (var cohortIdx: number = 0; cohortIdx < sourceCohortsDisplayData.length; cohortIdx++) {
            // start drawing links from the top of the source cohort rectangle
            var y0: number = source.y + sourceCohortsDisplayData[cohortIdx].y;

            links.forEach((link: MultiLink) => {
                var target: MultiNode = link.target;
                var targetCohortDisplayData: CohortDisplayData =
                    target.cohortNodesDisplayData[cohortIdx];

                var x1: number = target.x - this.nodeWidth/2;
                var xi: any = d3.interpolateNumber(x0, x1);
                var x2: number = xi(curvature);
                var x3: number = xi(1 - curvature);

                y0 += targetCohortDisplayData.height/2;
                var y1: number = target.y + targetCohortDisplayData.y +
                    targetCohortDisplayData.height/2;

                targetCohortDisplayData.linkPath = "M" + x0 + "," + y0
                    + "C" + x2 + "," + y0
                    + " " + x3 + "," + y1
                    + " " + x1 + "," + y1;

                // prepare y0 for next iteration
                y0 += targetCohortDisplayData.height/2;
            });
        }
    }
    /**
     * Given a raw thickness value in pixels, returns a thickness adjusted for
     * display.
     *
     * Args:
     *     originalThickness (number): The raw thickness in pixels.
     *
     * Returns:
     *     number: 1 if originalThickness in (0, 1], else originalThickness.
     */
    adjustThicknessForDisplay(originalThickness: number): number {
        var returnVal: number = originalThickness;
        if (originalThickness > 0) {
            returnVal = Math.max(originalThickness, 1);
        }
        return returnVal;
    }
    /**
     * Handles a click on a MultiNode by toggling the visibility of the node's
     * children and possibly updating the contents of the table.
     *
     * Args:
     *     node (MultiNode): The node that was clicked.
     */
    onNodeClick(node: MultiNode): void {
        if (node.children) {
            node.hideChildren(true);
            if (node == this.nodeForTable) {
                this.nodeForTable = null;
                window.scrollBy(-this.width, 0);
            }
        } else {
            // if the children are at the leaf level, display the table
            if (node.depth == this.levelNames.length + this.numTopHiddenLevels - 1) {
                // if we already have a `nodeForTable`, collapse it
                if (this.nodeForTable !== null) {
                    // showChildren below will pass `true` to trigger the update
                    this.nodeForTable.hideChildren(false);
                }
                this.nodeForTable = node;
                // scroll the container to the right
                // need to delay it slightly so the table is actually drawn,
                // overflowing the container, before we can scroll it
                // scroll the window to the top, too--no need for a delay, but
                // fewer jumps if we do all the scrolling at once
                setTimeout(() => {
                    window.scrollBy(this.width, -this.currentHeight);
                }, 200);
            }
            node.showChildren(true);
        }
        // stream will push a new MultiNode, which will trigger an update()
    }
}
