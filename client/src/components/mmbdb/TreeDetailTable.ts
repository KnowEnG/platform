import {Component, Input, OnChanges, SimpleChange} from '@angular/core';
import {Observable} from 'rxjs/Observable';
import {AbundanceBarChart} from './AbundanceBarChart';
import {DifferenceBarChart} from './DifferenceBarChart';
import {GroupedBarChart, GroupedBarChartDataRecord} from './GroupedBarChart';
import {MultiNode, CohortDisplayInfo, RELATIVE_ABUNDANCE_BIN_PROPERTY_SET} from '../../models/mmbdb/MultiNode';

@Component ({
    moduleId: module.id,
    selector: 'tree-detail-table',
    styleUrls: ['./TreeDetailTable.css'],
    templateUrl: './TreeDetailTable.html'
})

export class TreeDetailTable implements OnChanges {
    class = 'relative';

    /**
     * The MultiNode object representing the parent of all items in the table.
     */
    @Input()
    parentNode: MultiNode;

    /**
     * Number of top OTUs to show.
     */
    @Input()
    topOtuThreshold: number;

    /** The number of cohorts in the comparison. */
    numCohorts: number = 2;

    /** The rows of data for the table. */
    tableRows: TableRow[] = [];

    /** The options for the left and right sides of the difference column. */
    differenceOptions: Array<{label: string, style: string}> = [
        {label: "Cohort 1", style: "cohort-comparison"},
        {label: "Baseline", style: "cohort-baseline"},
        {label: "Individual", style: "cohort-patient"},
    ];

    /** The current index into `differenceOptions` for the left side. */
    differenceOptionsIndexLeft: number = 0;

    /** The current index into `differenceOptions` for the right side. */
    differenceOptionsIndexRight: number = 1;

    /** Whether we're currently waiting for data to load. */
    loading: boolean = true;

    /** The cohort labels and ordering required for GroupedBarChart. */
    cohortDisplayInfo: CohortDisplayInfo[];

    /**
     * Constructor.
     */
    constructor() {
    }
    /** Handles updates to the inputs. */
    ngOnChanges(changes: {[propertyName: string]: SimpleChange}) {
        // if parentNode changed, fetch its descendants
        var reload: boolean = false;
        for (let propName in changes) {
            if (propName == 'parentNode') {
                reload = true;
                break;
            }
        }
        if (reload) {
            this.loadData();
        } else {
            this.buildTableRows();
        }
    }
    /**
     * Fetches children and grandchildren of `parentNode`, calling `update()`
     * when done.
     */
    loadData(): void {
        this.tableRows = [];
        this.loading = true;
        this.numCohorts = this.parentNode.cohortNodes.length;
        // note MultiNode stores cohort nodes as they appear top to bottom in
        // the tree; i.e., Comparison, Baseline, Individual
        // GroupedBarChart needs them ordered Baseline, Comparison, Individual
        // this rearranges and labels them for GroupedBarChart
        this.cohortDisplayInfo = [
            {label: "Baseline", index: 1},
            {label: "Cohort 1", index: 0},
            {label: "Individual", index: 2}
        ].slice(0, this.numCohorts);
        var stream: Observable<number> = null;
        // check whether we have children and grandchildren
        if (this.parentNode.fetchedChildren === null) {
            stream = MultiNode.fetchChildren([this.parentNode]);
        } else {
            var childrenWithoutGrandchildren: MultiNode[] =
                MultiNode.filterParents(this.parentNode.fetchedChildren);
            if (childrenWithoutGrandchildren.length != 0) {
                stream = MultiNode.fetchChildren(childrenWithoutGrandchildren);
            }
        }
        // are we waiting for data?
        if (stream === null) {
            this.loading = false;
            this.update();
        } else {
            stream.subscribe(
                (count: number) => {
                    if (count !== null) {
                        this.loadData();
                    }
                },
                (err) => alert(err)
            );
        }
    }
    /**
     * Updates the view.
     */
    update(): void {
        this.buildTableRows();
    }
    /**
     * Assembles the children and grandchildren of `parentNode` into
     * `tableRows`.
     */
    public buildTableRows(): void {
        this.tableRows = [];
        this.parentNode.fetchedChildren.forEach((child) => {
            child.fetchedChildren.forEach((grandchild) => {
                var otuRank: number = grandchild.comparisonNode.topOtus[0] + 1;
                this.tableRows.push(new TableRow(
                    otuRank <= this.topOtuThreshold,
                    this.getPrettySpeciesName(child, grandchild),
                    otuRank,
                    false, // TODO: flagged
                    grandchild.cohortNodes.map((node) => node.relativeAbundanceMean),
                    grandchild.getDistributionData(this.cohortDisplayInfo, RELATIVE_ABUNDANCE_BIN_PROPERTY_SET),
                    this.getPrettyOTUName(grandchild)
                ));
            });
        });
    }
    /** Advances to the next option in `differenceOptions` for the left side. */
    public advanceDifferenceLeft(): void {
        this.differenceOptionsIndexLeft =
            (this.differenceOptionsIndexLeft + 1) % this.numCohorts;
    }
    /** Advances to the next option in `differenceOptions` for the right side. */
    public advanceDifferenceRight(): void {
        this.differenceOptionsIndexRight =
            (this.differenceOptionsIndexRight + 1) % this.numCohorts;
    }
    /** Given a species-level node and an OTU-level node, returns a species name ready to display in the table. */
    public getPrettySpeciesName(child: MultiNode, grandchild: MultiNode): string {

        // note: we can't rely on `grandchild.parent` to give us `child`, because
        // the `parent` field is only populated by the d3 tree layout code, which
        // hasn't been called on nodes at these levels

        var returnVal: string;

        // first, shorten to "E. coli" format; note "unclassified" is unaffected
        // typical: [A-Z][a-z]+_[a-z]+
        // unknown: "unclassified"
        // unusual (complete list from first data set):
        // 1. Bulleidia_hoa12_73A10
        // 2. Bulleidia_p-1630-c5
        // 3. Candidatus_Liberibacter_americanus (Ca. L. americanus)
        // 4. Candidatus_Phytoplasma_australiense (Ca. P. australiense)
        // 5. Desulfovibrio_C21_c20
        // 6. Desulfovibrio_D168
        // 7. Sharpea_p-3329-23G2

        // split at _
        var pieces: string[] = child.comparisonNode.name.split('_');
        if (pieces.length == 1) {
            // this is "unclassified"
            returnVal = pieces[0];
        } else if (pieces.length == 2) {
            // this is all typical cases and unusual cases 2, 6, and 7
            returnVal = pieces[0][0] + ". " + pieces[1];
        } else if (pieces.length == 3) {
            if (pieces[0] == "Candidatus") {
                // unusual cases 3 and 4
                returnVal = "Ca. " + pieces[1][0] + ". " + pieces[2];
            } else {
                // unusual cases 1 and 5
                returnVal = pieces[0][0] + ". " + pieces.slice(1).join(' ');
            }
        } else {
            // take a guess that it's like cases 1 and 5 but with more pieces
            returnVal = pieces[0][0] + ". " + pieces.slice(1).join(' ');
        }

        // if there are multiple OTUs sharing this species name, disambiguate
        // by appending the OTU number
        if (child.fetchedChildren.length > 1) {
            returnVal += ' (' + this.getPrettyOTUName(grandchild) + ')';
        }

        return returnVal;
    }
    /** Given an OTU-level node, returns an OTU name ready to display in the table. */
    public getPrettyOTUName(grandchild: MultiNode): string {
        return grandchild.comparisonNode.name.replace(/^OTU-/, '');
    }
}

class TableRow {
    constructor(
        public isTopFeature: boolean,
        public name: string,
        public rank: number,
        public isFlagged: boolean,
        public abundanceMeans: number[],
        public distribution: GroupedBarChartDataRecord[],
        public uid: string) {
    }
}
