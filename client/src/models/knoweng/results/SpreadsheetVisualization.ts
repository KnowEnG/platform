/*
 * 1. CLASSES REPRESENTING RAW DATA
 */

/** Represents one row of data. */
export class Row {
    constructor(
            public values: any[], // ordered as they appear in the original spreadsheet
            public idx: number, // row index in original spreadsheet
            public spreadsheet: Spreadsheet) {
    }
    getValuesOrderedBySampleNames(): any[] {
        return this.spreadsheet.orderedSampleIndices.map((idx: number) => {
            return idx !== null ? this.values[idx] : null;
        });
    }
    // TODO could clean up duplicated code in the next four methods
    // (note different return types)
    // copy and paste sure is fast, though
    getName(): string {
        let parentArray = this.spreadsheet.rowNames;
        let returnVal: string = null;
        if (parentArray !== null && parentArray.length > this.idx) {
            returnVal = parentArray[this.idx];
        }
        return returnVal;
    }
    getType(): string {
        let parentArray = this.spreadsheet.rowTypes;
        let returnVal: string = null;
        if (parentArray !== null && parentArray.length > this.idx) {
            returnVal = parentArray[this.idx];
        }
        return returnVal;
    }
    getVariance(): number {
        let parentArray = this.spreadsheet.rowVariances;
        let returnVal: number = null;
        if (parentArray !== null && parentArray.length > this.idx) {
            returnVal = parentArray[this.idx];
        }
        return returnVal;
    }
    getCorrelation(): number {
        let parentArray = this.spreadsheet.rowCorrelations;
        let returnVal: number = null;
        if (parentArray !== null && parentArray.length > this.idx) {
            returnVal = parentArray[this.idx];
        }
        return returnVal;
    }
    static compareValues(valA: any, valB: any, ascending = true): number {
        let returnVal: number;
        //Special consideration for missing value (null): it will be considered as 'biggest' than the other non-null value
        if (valA == null && valB != null)   
            returnVal = 1;
        else if (valA != null && valB == null)
            returnVal = -1;
        else if (ascending)
            returnVal = d3.ascending(valA, valB);
        else
            returnVal = d3.descending(valA, valB);
        //Hopefully we will not run into this, but comparing different types such as 2 with 'abc' will result in NaN. 
        //If such case happens, we will assume character is bigger than number.
        if (isNaN(returnVal)) {
            if(isNaN(valA) && !isNaN(valB))
                returnVal = -1;
            else
                returnVal = 1;
        }
        return returnVal;
    }
    static equal(one: Row, two: Row): boolean {
        if (one && two) {
            return one.spreadsheet.spreadsheetId == two.spreadsheet.spreadsheetId && one.idx == two.idx;
        }
        return one == two; // both null/undefined
    }
}

/** Represents one row of categoric data. */
export class CategoricRow extends Row {
    private distinctValues: string[];
    constructor(
            values: string[], // ordered as they appear in the original spreadsheet
            idx: number, // row index in original spreadsheet
            spreadsheet: Spreadsheet) {
        super(values, idx, spreadsheet);
        // next few lines borrowed from sample_clustering/HeatmapPane.ts
        // TODO redo SC visualization with SSV components
        let unsortedDistinctValues = Array.from((new Set(values)).values());
        this.distinctValues = unsortedDistinctValues.sort((valA: string, valB: string) => {
            return Row.compareValues(valA, valB, true);
        });
    }
    getDistinctValues(): string[] {
        let returnVal = Array.from(this.distinctValues);
        if (returnVal[returnVal.length-1] !== null &&
                this.values.length < this.spreadsheet.orderedSampleIndices.length) {
            // in the original spreadsheet, this row didn't contain missing values
            // however, this spreadsheet doesn't contain all of the samples being
            // shown on screen, so we'll have missing values for those new samples
            // add null to the returned array
            returnVal.push(null);
        }
        return returnVal;
    }
}

/** Represents one row of numeric data. */
export class NumericRow extends Row {
    private minValue: number;
    private maxValue: number;
    constructor(
            values: number[], // ordered as they appear in the original spreadsheet
            idx: number, // row index in original spreadsheet
            spreadsheet: Spreadsheet) {
        super(values, idx, spreadsheet);
        let extent = d3.extent(values);
        this.minValue = extent[0];
        this.maxValue = extent[1];
    }
    getMin(): number { return this.minValue; }
    getMax(): number { return this.maxValue; }
}

export class Spreadsheet {
    private numRows: number;
    private sampleNameToIndexMap: d3.Map<number> = d3.map<number>();
    // public for service's use, not component's use
    public rowIdxToRowMap: d3.Map<Row> = d3.map<Row>();
    /** column indices into this.sampleNames to match state.orderedSampleNames; null for NA */
    public orderedSampleIndices: number[];
    public filteredAndSortedRows: NumericRow[]; // could move this
    public rowOriginalRanks: number[]; // revisit if/when we add more filter/sort types
    constructor(
            public spreadsheetId: number,
            public fileId: number, // confirm int, not string TODO
            public rowNames: string[], // all row names ordered as they appear in the source file
            public rowTypes: string[],
            public rowVariances: number[], // consider moving to view state
            public rowCorrelations: number[], // consider moving to view state // TODO -log10(pval)?
            public sampleNames: string[], // ordered as they appear in the source file
            public isTransposed: boolean,
            public rowNanCounts: number[],
            public columnNanCounts: number[]
        ) {
        this.numRows = rowNames.length;
        this.sampleNames.forEach((name: string, idx: number) => this.sampleNameToIndexMap.set(name, idx));
        this.rowOriginalRanks = this.rowNames.map((name, index) => (this.numRows - index)/this.numRows);
    }
    isEligibleForMainHeatmap(): boolean {
        // TODO revisit for numerically-coded categorical spreadsheets
        return this.rowTypes.filter((rt: string) => rt == "numeric").length == this.rowTypes.length;
    }
    /** updates this.orderedSampleIndices; called by service */
    updateSampleOrder(orderedSampleNames: string[]): void {
        this.orderedSampleIndices = orderedSampleNames.map((name: string) => {
            return this.sampleNameToIndexMap.has(name) ? this.sampleNameToIndexMap.get(name) : null;
        });
    }
   getFilteredMin(): number {
       // TODO more efficient implementation?
       return d3.min(this.filteredAndSortedRows, (row: NumericRow) => row.getMin());
   }
   getFilteredMax(): number {
       // TODO more efficient implementation?
       return d3.max(this.filteredAndSortedRows, (row: NumericRow) => row.getMax());
   }
   getRowIndxToRowSubmap(indices: number[]): d3.Map<Row> {
        let submap: d3.Map<Row> = d3.map<Row>();
        indices.forEach((idx: number) => {
           this.rowIdxToRowMap.has(''+idx) ? submap.set(''+idx, this.rowIdxToRowMap.get(''+idx)) : submap.set(''+idx, null)
           });
        return submap;
   }
}

/*
 * 2. CLASSES REPRESENTING VIEW STATE
 */

export class SSVStateRequest {
    constructor(
        public columnGroupingRowRequest: RowStateRequest,
        public columnSortingRowRequest: RowStateRequest,
        public mainSpreadsheetStateRequests: MainSpreadsheetStateRequest[],
        public otherRowStateRequests: RowStateRequest[],
        public timeToEventEventRowRequest: RowStateRequest,
        public timeToEventTimeRowRequest: RowStateRequest,
        public timeToEventEventValue: string, // this isn't async but is a step toward ngrx
        public timeToEventPvalRequests: RowStateRequest[],
        public endJobRequest: EndJobRequest) {
    }
    copy(): SSVStateRequest {
        // Handle null for both options
        let group = this.columnGroupingRowRequest ? this.columnGroupingRowRequest.copy() : null;
        let sort = this.columnSortingRowRequest ? this.columnSortingRowRequest.copy() : null;
        let event = this.timeToEventEventRowRequest ? this.timeToEventEventRowRequest.copy() : null;
        let time = this.timeToEventTimeRowRequest ? this.timeToEventTimeRowRequest.copy() : null;
        let endJobRequest = this.endJobRequest ? this.endJobRequest.copy() : null;
        return new SSVStateRequest(
            group,
            sort,
            this.mainSpreadsheetStateRequests.map((mssr) => mssr.copy()),
            this.otherRowStateRequests.map((orsr) => orsr.copy()),
            event,
            time,
            this.timeToEventEventValue,
            this.timeToEventPvalRequests.map((pr) => pr.copy()),
            endJobRequest);
    }
}

export enum FilterType {VARIANCE, CORRELATION_TO_GROUP, SPREADSHEET_ORDER}
export enum SortType {VARIANCE, CORRELATION_TO_GROUP, SPREADSHEET_ORDER}

export class MainSpreadsheetStateRequest {
    constructor(
        public spreadsheetId: number,
        public filterType: FilterType,
        public filterLimit: number,
        public sortType: SortType) {
    }
    copy(): MainSpreadsheetStateRequest {
        return new MainSpreadsheetStateRequest(
            this.spreadsheetId,
            this.filterType,
            this.filterLimit,
            this.sortType);
    }
    static equal(one: MainSpreadsheetStateRequest, two: MainSpreadsheetStateRequest): boolean {
        if (one && two) {
            return one.spreadsheetId == two.spreadsheetId &&
                one.filterType == two.filterType &&
                one.filterLimit == two.filterLimit &&
                one.sortType == two.sortType;
        }
        return one == two; // both null/undefined
    }
}

export class RowStateRequest {
    constructor(
        public spreadsheetId: number,
        public rowIdx: number) {
    }
    copy(): RowStateRequest {
        return new RowStateRequest(
            this.spreadsheetId,
            this.rowIdx);
    }
    static equal(one: RowStateRequest, two: RowStateRequest): boolean {
        if (one && two) {
            return one.spreadsheetId == two.spreadsheetId && one.rowIdx == two.rowIdx;
        }
        return one == two; // both null/undefined
    }
}

export class EndJobRequest {
    constructor(public jobId: number) {
    }
    copy(): EndJobRequest {
        return new EndJobRequest(
            this.jobId);
    }
}

export interface TimeToEventPvalue {
    request: RowStateRequest,
    pval: number
}

export class SSVState {
    public orderedSampleNames: string[];
    public timeToEventEventValue: string; // this isn't async but is a step toward ngrx
    constructor(
            public spreadsheets: Spreadsheet[],
            public columnGroupingRow: CategoricRow,
            public columnSortingRow: Row,
            public otherRows: Row[],
            public timeToEventEventRow: Row,
            public timeToEventTimeRow: NumericRow,
            public timeToEventPvals: TimeToEventPvalue[],
            public stateRequest: SSVStateRequest) {
        this.timeToEventEventValue = stateRequest ? stateRequest.timeToEventEventValue : null;
        // set orderedSampleNames
        // TODO move to service, and only do when grouping/sorting changes?
        // first, get the union of all sample names
        let allSampleNamesSet = new Set<string>();
        spreadsheets.forEach((ss) => {
            ss.sampleNames.forEach((name) => allSampleNamesSet.add(name));
        });
        let allSampleNames = Array.from(allSampleNamesSet.values());
        // second, sort the names
        // keep in mind that...
        // - the grouping row might contain missing values and/or not contain
        //   all sample names; put all of these in a new group after the last
        //   group
        // - the sorting row might contain missing values and/or not contain
        //   all sample names; put all of these at the end of their groups
        // create a mapping from sample name to grouping value
        let sampleNameToGroupValueMap: d3.Map<string> = d3.map<string>();
        if (columnGroupingRow && columnGroupingRow.spreadsheet) {
            let sampleNames = columnGroupingRow.spreadsheet.sampleNames;
            let values = columnGroupingRow.values;
            sampleNames.forEach((name, idx) => {
                sampleNameToGroupValueMap.set(name, values[idx]);
            });
        } else {
            // map all samples to the same value
            allSampleNames.forEach((name) => {
                sampleNameToGroupValueMap.set(name, "");
            });
        }
        // create a mapping from sample name to sorting value
        let sampleNameToSortValueMap: d3.Map<any> = d3.map<any>();
        if (columnSortingRow && columnSortingRow.spreadsheet) {
            let sampleNames = columnSortingRow.spreadsheet.sampleNames;
            let values = columnSortingRow.values;
            sampleNames.forEach((name, idx) => {
                sampleNameToSortValueMap.set(name, values[idx]);
            });
        } else {
            // map all samples to the same value
            allSampleNames.forEach((name) => {
                sampleNameToSortValueMap.set(name, 0);
            });
        }
        // do the sort
        this.orderedSampleNames = allSampleNames.sort((valA: string, valB: string) => {
            // check grouping values first (note compareValues will put nulls
            // last, where we want them)
            let groupValA = sampleNameToGroupValueMap.has(valA) ? sampleNameToGroupValueMap.get(valA) : null;
            let groupValB = sampleNameToGroupValueMap.has(valB) ? sampleNameToGroupValueMap.get(valB) : null;
            let returnVal = Row.compareValues(groupValA, groupValB, true);
            // if group values tie, check sorting values second (again w/ nulls last)
            // TODO descending sort for numeric rows?
            if (returnVal == 0) {
                let sortValA = sampleNameToSortValueMap.has(valA) ? sampleNameToSortValueMap.get(valA) : null;
                let sortValB = sampleNameToSortValueMap.has(valB) ? sampleNameToSortValueMap.get(valB) : null;
                returnVal = Row.compareValues(sortValA, sortValB, true);
            }
            return returnVal;
        });
        this.spreadsheets.forEach((spreadsheet) => {
            spreadsheet.updateSampleOrder(this.orderedSampleNames);
        });
    }

    /**
     * Get the spreadsheet object in a state by spreadsheet id
     */
    getSpreadsheet(spreadsheetId: number) {
        if (this.spreadsheets) {
            for (let i = 0; i < this.spreadsheets.length; i++) {
                if(this.spreadsheets[i].spreadsheetId == spreadsheetId)
                    return this.spreadsheets[i];
            }
        }
        return null;
    }
}


/*
 * 3. ??? TODO need to sort through what's left here--anything useful?
 */

// /** Represents a range of array indices. */
// export class IndexRange {
//     constructor(public firstIndex: number, public lastIndex: number) { }
// }

// /** Represents a group as defined by a categorical row as selected by the user. */
// export class Group {
//     public isHidden = false;
//     constructor(
//         public groupNumber: number,
//         public groupValue: string,
//         public sampleIndexRange: IndexRange) {
//     }
//     /** Returns this.groupNumber formatted for display. */
//     getGroupNumberLabel(): string { return "G" + this.groupNumber; }
//     hide(): void { this.isHidden = true; }
//     show(): void { this.isHidden = false; }
//     /** Produces Groups for current grouping; to be called when grouping changes. */
//     static groupsForRow(groupingRow: CategoricRow): Group[] {
//         //FIXME
//         return [];
//     }
// }

/** Represents the state of the visualization. */
// export class SSVState {
//     /** from Group.groupsForRow(this.columnSortingRow), set by this.setColumnSortingRow() */
//     groups: Group[] = null;
//     orderedSampleNames: string[]; // ordering based on grouping and sorting, unaffected by visible ranges
//     visibleSampleIndexRanges: IndexRange[]; // affected by slider and group-level zoom,
//     getOrderedVisibleSampleNames: string[];
//     isBirdseye: boolean; // (true, false, null if disabled?),
//     spreadsheets: Spreadsheet[];
//     mainSpreadsheetHeatmapStates: MainSpreadsheetHeatmapState[] = []; // ordered for display
//     singleRowHeatmapStates: SingleRowHeatmapState[]; // ordered for display,
// }

// export class MainSpreadsheetHeatmapState {
//     public areLabelsVisible = true;
//     public filterType: FilterType;
//     public sortType: SortType;
//     private filteredAndSortedRows: NumericRow[] = null;
//     /** called when first drawing screen and when user enables previously disabled main spreadsheet */
//     constructor(public spreadsheet: Spreadsheet, public filterLimit: number) {
//         this.filterType = FilterType.VARIANCE;
//         this.sortType = SortType.VARIANCE;
//     }
// }


/*
REMINDERS

on loading...
    x call the jobs_spreadsheets endpoint to get spreadsheet_ids
    x call the spreadsheets endpoint to populate our Spreadsheet[]
    x call the variances endpoint for our eligible spreadsheets to update Spreadsheet[]
    x determine sample names union
    - determine number of rows to load per main spreadsheet
    - call the row data endpoint to fetch the top rows by variance per main spreadsheet

on showing a single-row heatmap...
    - call endpoint to update state
    x fetch row data, if not already in memory

on hiding a single-row heatmap...
    - call endpoint to update stat
    x release from memory, if not needed elsewhere (col grouping, col sorting, main heatmaps); probably leave it to the GC for starters but could try something clever

on changing the basis for column grouping...
    - call endpoint to update state
    x do the usual things for hiding a single-row heatmap (if previous basis was not null) and showing a single-row heatmap
    x update correlations on Spreadsheet[]
    - make sure updating correlations in Spreadsheet[] in turn updates scores next to dist graphs and in the row-picker
    x if any current row filtering uses correlation, redo (might involve calling row data endpoint)
    x if any current row sorting uses correlation, redo
    x reorder columns in heatmaps

on changing the basis for column sorting...
    - call endpoint to update state
    x do the usual things for hiding a single-row heatmap (if previous basis was not null) and showing a single-row heatmap
    x reorder columns in heatmaps

on changing the row filter type...
    - call the endpoint to update state
    x fetch new rows
    x re-sort rows
    - make sure area graph data updated

on changing the row filter limit...
    - call the endpoint to update state
    x fetch new rows
    x (re-)sort (/new) rows

on changing the row sort type...
    - call the endpoint to update state
    x re-sort rows


SCREEN ELEMENTS


Show spreadsheets dropdown:
- List eligible (state.spreadsheets.filter(isEligibleForMainHeatmap)
- Checkboxes
   - Checked property (spreadsheet in state.mainSpreadsheetHeatmapStates)
   - Onchange (add/remove spreadsheet to state.mainSpreadsheetHeatmapStates using MainSpreadsheetHeatmapState constructor)

Show columns slider:
- Num columns (state.orderedSampleNames.length)
- Currently selected range (state.visibleSampleIndexRanges -- NEED TO CONFIRM W/ LISA HOW SLIDER SHOULD INTERACT WITH GROUP-LEVEL ZOOM CONTROLS -- review her comment on https://projects.invisionapp.com/d/#/console/11370914/260379479/comments/88535928)
- Show birdseye checkbox (state.isBirdseye)

Group columns control:
- SEE Row picker
- Current value w/ row name (state.columnGroupingRow, which has getName())

Group column HM:
- Group labels (state.groups[index].getGroupNumberLabel() etc.)
- Group ranges (state.groups[index].sampleIndexRange)
- Group range zoom controls (stage.groups[index].show()/hide()/isHidden)
- SEE Single-row heatmap

Sort columns control:
- SEE Row picker

Sort columns HM:
- SEE Single-row heatmap

Main heatmap area:
- Ordered list of main heatmaps (state.mainSpreadsheetHeatmapStates)

Main heatmap:
- Labels checkbox (state.mainSpreadsheetHeatmapStates[index].areLabelsVisible)
- File name (state.mainSpreadsheetHeatmapStates[index].spreadsheet.file_id -> file name pipe)
- Info button (TODO -- NEED INFO FROM LISA)
- Filter type (state.mainSpreadsheetHeatmapStates[index].filterType)
- Filter limit (state.mainSpreadsheetHeatmapStates[index].filterLimit)
- Filter area graph (state.mainSpreadsheetHeatmapStates[index].spreadsheet.rowVariances/rowCorrelations, sorted)
- Sort type (state.mainSpreadsheetHeatmapStates[index].sortType)
- Filtered and sorted rows (state.mainSpreadsheetHeatmapStates[index].getFilteredAndSortedRows())
- Sorted columns (state.orderedSampleNames)
- Ordered/windowed values (state.mainSpreadsheetHeatmapStates[index].getFilteredAndSortedRows().map(=> getValuesOrderedBySampleNames()))
- Ordered/windowed values as colors (ordered/windowed values passed through state.mainSpreadsheetHeatmapStates[index].getColorScale())
- Color scale (state.mainSpreadsheetHeatmapStates[index].getColorScale())
- SEE Main heatmap rollover

Main heatmap rollover:
- TODO coming later; no comp yet

Show rows control:
- SEE Row picker

Single-row heatmap area:
- ordered list of SR heatmaps

Single-row heatmap:
- Ordered/windowed values (row.getValuesOrderedBySampleNames())
- Ordered/windowed colors (row.getValuesOrderedBySampleNames() passed through rowState.getColorScale())
- Color scale (numeric and categorical cases)
- SEE Single-row heatmap rollover
- Distribution graph
   - Row name (row.getName())
   - Continuous
      - Min, max (row.getMin(), row.getMax())
      - Gradient (rowState.getColorScale())
      - Values split to bins (row.values to d3)
      - Counts per bin (row.values to d3)
      - Percentages per bin (row.values to d3)
      - Bin bounds (row.values to d3)
   - Categorical
      - Values (row.getDistinctValues())
      - Color assignments (rowState.getColorScale())
      - Counts per value (row.values to d3)
      - Percentages per value (row.values to d3)
- Correlation score if not grouping or sorting row (row.getCorrelation())

Single-row heatmap rollover:
- Row name (row.getName())
- File name (row.spreadsheet.fileId -> file name pipe)
- Number of samples (row.values.length OR count by union over all spreadsheets?)
- Continuous
   - Values (row.values)
   - Min, Max (row.getMin(), row.getMax())
   - Primary bins (row.values to d3)
   - Bin bounds per primary bin (row.values to d3)
   - Count per primary bin (row.values to d3)
   - Percentage per primary bin (row.values to d3)
   - Secondary bins (row.values to d3)
   - Count per secondary bin (row.values to d3)
   - Gradient (rowState.getColorScale())
   - Group names (state.groups.map(=> getGroupValue())
   - Samples per group (from state.groups.map(=> sampleIndexRange))
   - Samples per primary bin per group (from state.groups.map(=> sampleIndexRange) and row.getValuesOrderedBySampleNames())
- Categorical
   - Values (row.values)
   - Percentage per value (row.values to d3)
   - Count per value (row.values to d3)
   - Color assignments (rowState.getColorScale())
   - Group names (state.groups.map(=> getGroupValue())
   - Samples per group (from state.groups.map(=> sampleIndexRange))
   - Samples per value per group (from state.groups.map(=> sampleIndexRange) and row.getValuesOrderedBySampleNames())

Row picker
- Title (from context: grouping row, sorting row, or "Show Rows")
- List of spreadsheet names (state.spreadsheets[index].fileId -> file name pipe)
- Number selected rows per spreadsheet if "Show Rows" case (state.singleRowSpreadsheetStates.map(=> row.spreadsheet.fileId))
- Number total rows per spreadsheet, in order to enable/disable search field (spreadsheet.rowNames.length)
- Rows per spreadsheet, possibly filtered by type (iterating over spreadsheet.rowNames[i])
   - Checkbox per row
      - Checked property (rowIdx/spreadsheet.fileId in state.singleRowSpreadsheetStates)
      - Onchange -- HANDLE IMMEDIATELY OR WAIT UNTIL DONE?
         - If grouping
            - Call state.setColumnGroupingRow(row))
         - If sorting
            - Call state.setColumnSortingRow(row))
         - If "Show Rows"
            - Modify state.singleRowSpreadsheetStates
   - Name (spreadsheet.rowNames[i])
   - Score if "Show Rows" and grouping has been set (spreadsheet.rowCorrelations[i])


*/