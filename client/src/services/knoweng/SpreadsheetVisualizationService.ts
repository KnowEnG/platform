import {Injectable} from '@angular/core';
import {AuthHttp} from 'angular2-jwt';
import {Observable} from 'rxjs/Observable';
import {Subscription} from 'rxjs/Subscription';
import {BehaviorSubject} from 'rxjs/BehaviorSubject';

import 'rxjs/add/observable/forkJoin';
import 'rxjs/add/observable/of';

import {SSVState, SSVStateRequest, MainSpreadsheetStateRequest, RowStateRequest, Spreadsheet, Row, CategoricRow, NumericRow, FilterType, SortType, TimeToEventPvalue} from '../../models/knoweng/results/SpreadsheetVisualization';
import {EveUtilities} from '../common/EveUtilities';
import {LogService} from '../common/LogService';

@Injectable()
export class SpreadsheetVisualizationService {

    private _jobSpreadsheetsUrl: string = '/api/v2/ssviz_jobs_spreadsheets';
    private _spreadsheetsUrl: string = '/api/v2/ssviz_spreadsheets';
    private _rowDataUrl: string = '/api/v2/ssviz_feature_data';
    private _rowVariancesUrl: string = '/api/v2/ssviz_feature_variances';
    private _rowCorrelationsUrl: string ='/api/v2/ssviz_feature_correlations';
    private _survivalAnalysesUrl: string = '/api/v2/ssviz_survival_analyses';
    
    private _broadcast: BehaviorSubject<SSVState> = new BehaviorSubject<SSVState>(null);

    private _previousRequest: SSVStateRequest; // previous request for tracking changes
    private _processingRequest: SSVStateRequest; // request we're currently processing
    private _nextRequest: SSVStateRequest; // next request to process
    
    constructor(private authHttp: AuthHttp, private logger: LogService) {
    }

    // TODO: This has evolved into a mix of procedure-calling (e.g.,
    // getInitialSSVStateWithoutData) and message-passing (e.g., EndJobRequest).
    // Revisit all data flows in light of outside developments since our project
    // started, including library support like ngrx and progress toward best
    // practices for state management and async data.

    /**
     * First call on initial load, we will get all spreadsheet ids, row names, header names and variance scores if a spreadsheet has them
     *
     */
    getInitialSSVStateWithoutData(jobId: number): Observable<SSVState> {
        // clear request states--this is initialization
        this._previousRequest = null;
        this._processingRequest = null;
        this._nextRequest = null;
        // fetch the spreadsheets
        this.getSpreadsheetsForJobId(jobId)
            .subscribe(
                (spreadsheets: Spreadsheet[]) => {
                    this.updateSpreadsheetsWithVariances(spreadsheets).subscribe(
                        (spreadsheetsWithVariances: Spreadsheet[]) => {
                            let state: SSVState = new SSVState(
                                spreadsheetsWithVariances,
                                null, // column grouping row
                                null, // column sorting row
                                [], // other rows
                                null, // time-to-event event row
                                null, // time-to-event time row
                                [], // time-to-event pvals
                                null // state request
                            );
                            this._broadcast.next(state);
                        },
                        (error: any) => {
                            this.logger.error("Failed to get job result for: " + jobId, error.stack);
                        }
                    );        
                },
                (error: any) => {
                    this.logger.error(error.message, error.stack);
                }
            );
        return this._broadcast.asObservable();
    }
    
    /**
     * Fetch and massage data to satisfy a state request. Returns nothing but
     * will trigger an update on the Observable<SSVState> returned by the
     * previous call to getInitialSSVStateWithoutData.
     */
    updateSSVState(stateRequest: SSVStateRequest): void {
        this.addNextToRequestQueue(stateRequest);
    }

    /**
     * Adds new request to queue. Will start processing if queue consumer is
     * idle.
     * Note we don't really keep a queue currently; instead, we assume the only
     * request that matters is the latest request.
     */
    private addNextToRequestQueue(stateRequest: SSVStateRequest): void {
        this._nextRequest = stateRequest.copy();
        this.checkRequestQueue();
    }

    /**
     * Removes current request, now done, from queue. Will start processing the
     * next item if one exists.
     * Note we don't really keep a queue currently; instead, we assume the only
     * request that matters is the latest request.
     */
    private removeCurrentFromRequestQueue(): void {
        this._previousRequest = this._processingRequest;
        this._processingRequest = null;
        this.checkRequestQueue();
    }

    /**
     * Does any work waiting to be done.
     * Note we don't really keep a queue currently; instead, we assume the only
     * request that matters is the latest request.
     */
    private checkRequestQueue(): void {
        if (this._processingRequest === null && this._nextRequest !== null) {
            this._processingRequest = this._nextRequest;
            this._nextRequest = null;
            this.processNextRequest();
        }
    }

    private processNextRequest(): void {
        let stateRequest = this._processingRequest;
        if (stateRequest.endJobRequest != null) {
            this._broadcast.next(null);
            this.removeCurrentFromRequestQueue();   
        } else {
            this.updateSpreadsheetsWithCorrelations(stateRequest).subscribe(
                (corrServerCalls: number) => {
                    this.updateSpreadsheetsWithRowData(stateRequest).subscribe(
                        (rowsServerCalls: number) => {
                            this.getTimeToEventPvals(stateRequest).subscribe(
                                (pvals: TimeToEventPvalue[]) => {
                                    // publish a new value
                                    // we've cheated here a bit and recycled objects
                                    // from the last state--not necessary, but might
                                    // simplify things; if it doesn't, can change
                                    let currentState = this._broadcast.getValue();
                                    // create a map from spreadsheet id to spreadsheet obj
                                    let spreadsheetIdToSpreadsheet: d3.Map<Spreadsheet> = d3.map<Spreadsheet>();
                                    currentState.spreadsheets.forEach((ss) => spreadsheetIdToSpreadsheet.set("" + ss.spreadsheetId, ss));
                                    // create a function that returns the row obj for a row request
                                    let rowExtractor = (rowRequest: RowStateRequest) => {
                                        let returnVal: Row = null;
                                        if (rowRequest) {
                                            let ss = spreadsheetIdToSpreadsheet.get("" + rowRequest.spreadsheetId);
                                            returnVal = ss.rowIdxToRowMap.get("" + rowRequest.rowIdx);
                                        }
                                        return returnVal;
                                    };
                                    let newState = new SSVState(
                                        currentState.spreadsheets,
                                        <CategoricRow>rowExtractor(stateRequest.columnGroupingRowRequest),
                                        rowExtractor(stateRequest.columnSortingRowRequest),
                                        stateRequest.otherRowStateRequests.map((rr) => rowExtractor(rr)),
                                        rowExtractor(stateRequest.timeToEventEventRowRequest),
                                        <NumericRow>rowExtractor(stateRequest.timeToEventTimeRowRequest),
                                        pvals,
                                        stateRequest
                                    );
                                    this._broadcast.next(newState);
                                    this.removeCurrentFromRequestQueue();
                                },
                                (error: any) => {
                                    this.logger.error(error.message, error.stack);
                                    this.removeCurrentFromRequestQueue();
                                }
                            );
                        },
                        (error: any) => {
                            this.logger.error(error.message, error.stack);
                            this.removeCurrentFromRequestQueue();
                        }
                    );
                },
                (error: any) => {
                    this.logger.error(error.message, error.stack);
                    this.removeCurrentFromRequestQueue();
                }
            );
        }
    }

    /**
     * Updates current spreadsheets with correlation scores. Uses scores already
     * in memory if we have them, returning immediately, or else fetches them
     * from the server. Number in observable is number of correlations fetched
     * from server.
     */
    private updateSpreadsheetsWithCorrelations(stateRequest: SSVStateRequest): Observable<number> {
        let currentState: SSVState = this._broadcast.getValue();
        let groupingRequest = stateRequest.columnGroupingRowRequest;
        let spreadsheets = currentState.spreadsheets;
        if (this._previousRequest !== null) {
            // shortcut if grouping hasn't changed
            let currentGrouping = this._previousRequest.columnGroupingRowRequest;
            if (RowStateRequest.equal(currentGrouping, groupingRequest)) {
                return Observable.of(0);
            }
        }
        if (groupingRequest === null) {
            // shortcut if no grouping
            spreadsheets.forEach((ss) => ss.rowCorrelations = []);
            return Observable.of(0);
        }
        let ssids = spreadsheets.map((ss: Spreadsheet) => ss.spreadsheetId);
        let url = this._rowCorrelationsUrl + "?ssviz_spreadsheet_id=" + ssids.join()
                + "&g_spreadsheet_id=" + groupingRequest.spreadsheetId
                + "&g_feature_idx=" + groupingRequest.rowIdx;
        return this.authHttp
            .get(url)
            .map(res => {
                let items: any[] = res.json()._items;
                items.forEach((correlationDatum: any) => {
                    let matches = spreadsheets.filter(ss => ss.spreadsheetId == correlationDatum.ssviz_spreadsheet_id);
                    if (matches.length == 1) {
                        // using -10*log10 of pval, capped at 200--below we'll correct the value for grouping vs. self
                        matches[0].rowCorrelations = correlationDatum.scores.map((score: number) => Math.min(-10.0 * Math.log10(score), 200));
                        // represent grouping vs. self pval as Infinity
                        if (groupingRequest.spreadsheetId == correlationDatum.ssviz_spreadsheet_id) {
                            matches[0].rowCorrelations[groupingRequest.rowIdx] = Infinity;
                        }
                    } else {
                        this.logger.error("Got " + matches.length + " matches for " + correlationDatum.ssviz_spreadsheet_id);
                    }
                });
                return items.length;
            });
    }

    /**
     * Updates current spreadsheets with row data. Uses row data already
     * in memory if we have them, returning immediately, or else fetches them
     * from the server. Number in observable is number of rows fetched from
     * server.
     */
    private updateSpreadsheetsWithRowData(stateRequest: SSVStateRequest): Observable<number> {
        // create an observable for updating each spreadsheet
        let spreadsheetStreams = this._broadcast.getValue().spreadsheets.map((ss) => {
            return this.updateOneSpreadsheetWithRowData(ss, stateRequest);
        });
        // once all the spreadsheets have been updated, publish the total number of rows fetched
        return Observable.forkJoin(spreadsheetStreams).map((countsArray: number[]) => d3.sum(countsArray));
    }

    private getSingleRowIdxsForSpreadsheet(spreadsheet: Spreadsheet, stateRequest: SSVStateRequest): number[] {
        let singleRowRequests = stateRequest.otherRowStateRequests.filter((rr) => {
            return rr.spreadsheetId == spreadsheet.spreadsheetId;
        });
        [
            stateRequest.columnGroupingRowRequest,
            stateRequest.columnSortingRowRequest,
            stateRequest.timeToEventEventRowRequest,
            stateRequest.timeToEventTimeRowRequest
        ].forEach((request) => {
            if (request && request.spreadsheetId == spreadsheet.spreadsheetId) {
                singleRowRequests.push(request);
            }
        });
        return singleRowRequests.map((rr) => rr.rowIdx);
    }

    /**
     * Updates one current spreadsheet with row data. Responsible for both the
     * main heatmap rows and any single-row heatmap rows from the spreadsheet.
     * Uses row data already in memory if we have them, returning immediately,
     * or else fetches them from the server. Number in observable is number of
     * rows fetched from server.
     */
    private updateOneSpreadsheetWithRowData(spreadsheet: Spreadsheet, stateRequest: SSVStateRequest): Observable<number> {
        let currentState = this._broadcast.getValue();
        let spreadsheetStateRequest = stateRequest.mainSpreadsheetStateRequests.filter((mssr) => mssr.spreadsheetId == spreadsheet.spreadsheetId)[0];
        let singleRowIdxs = this.getSingleRowIdxsForSpreadsheet(spreadsheet, stateRequest);
        // collect a few details about the last request for comparison
        let lastSpreadsheetStateRequest: MainSpreadsheetStateRequest = null;
        let lastSingleRowIdxs: number[] = [];
        let lastColumnGrouping: RowStateRequest = null;
        let lastColumnSorting: RowStateRequest = null;
        if (this._previousRequest !== null) {
            lastSpreadsheetStateRequest = this._previousRequest.mainSpreadsheetStateRequests.filter((mssr) => mssr.spreadsheetId == spreadsheet.spreadsheetId)[0];
            lastSingleRowIdxs = this.getSingleRowIdxsForSpreadsheet(spreadsheet, this._previousRequest);
            lastColumnGrouping = this._previousRequest.columnGroupingRowRequest;
            lastColumnSorting = this._previousRequest.columnSortingRowRequest;
        }
        if (lastSpreadsheetStateRequest == null ||
                // filter changed
                (spreadsheetStateRequest && spreadsheetStateRequest.filterType !== lastSpreadsheetStateRequest.filterType) ||
                (spreadsheetStateRequest && spreadsheetStateRequest.filterLimit !== lastSpreadsheetStateRequest.filterLimit) ||
                // sort changed -- we won't call server, but we will re-sort
                (spreadsheetStateRequest && spreadsheetStateRequest.sortType !== lastSpreadsheetStateRequest.sortType) ||
                // single-row heatmaps from this spreadsheet have changed
                // TODO less lazy check?
                singleRowIdxs.join() != lastSingleRowIdxs.join() ||
                // column grouping has changed
                !RowStateRequest.equal(lastColumnGrouping, stateRequest.columnGroupingRowRequest) ||
                // column sorting has changed
                // even if we don't need new data from the server, we should
                // update filteredAndSortedRows--that's our contract for change-
                // detection
                !RowStateRequest.equal(lastColumnSorting, stateRequest.columnSortingRowRequest)) {
            let rowIdxsToFetch = new Set<number>([]); // rows we need from server
            let rowIdxsToKeep = new Set<number>([]); // rows to keep from current mem
            let mainHeatmapIdxs: number[] = [];
            if (spreadsheet.isEligibleForMainHeatmap() && spreadsheetStateRequest) {
                // determine the ordered row idxs needed for filter/sort based on
                // filterType, filterLimit, sortType, and rowVariances/rowCorrelations
                let filterScores: number[];
                if (spreadsheetStateRequest.filterType == FilterType.VARIANCE) {
                    filterScores = spreadsheet.rowVariances;
                } else if (spreadsheetStateRequest.filterType == FilterType.CORRELATION_TO_GROUP) {
                    filterScores = spreadsheet.rowCorrelations;
                } else if (spreadsheetStateRequest.filterType == FilterType.SPREADSHEET_ORDER) {
                    filterScores = spreadsheet.rowOriginalRanks;
                } else {
                    this.logger.error("Unknown filter type " + spreadsheetStateRequest.filterType);
                    return Observable.of(0);
                }
                let sortScores: number[];
                if (spreadsheetStateRequest.sortType == SortType.VARIANCE) {
                    sortScores = spreadsheet.rowVariances;
                } else if (spreadsheetStateRequest.sortType == SortType.CORRELATION_TO_GROUP) {
                    sortScores = spreadsheet.rowCorrelations;
                } else if (spreadsheetStateRequest.sortType == SortType.SPREADSHEET_ORDER) {
                    sortScores = spreadsheet.rowOriginalRanks;
                } else {
                    this.logger.error("Unknown filter type " + spreadsheetStateRequest.filterType);
                    return Observable.of(0);
                }

                // collect idx, filter, and sort scores as object per row
                let combinedScores = filterScores.map((filterScore, idx) => {
                    return {idx: idx, filterScore: filterScore, sortScore: sortScores[idx]};
                });
                // apply filtering
                combinedScores.sort((a, b) => d3.descending(a.filterScore, b.filterScore));
                combinedScores = combinedScores.slice(0, spreadsheetStateRequest.filterLimit);
                // apply sorting
                combinedScores.sort((a, b) => d3.descending(a.sortScore, b.sortScore));

                // translate into ordered row idxs
                mainHeatmapIdxs = combinedScores.map((obj) => obj.idx);

                mainHeatmapIdxs.forEach((rowIdx) => {
                    if (spreadsheet.rowIdxToRowMap.has("" + rowIdx)) {
                        rowIdxsToKeep.add(rowIdx);
                    } else {
                        rowIdxsToFetch.add(rowIdx);
                    }
                });
            }
            // handle any single-row heatmaps from this spreadsheet
            let singleRowIdxs = this.getSingleRowIdxsForSpreadsheet(spreadsheet, stateRequest);
            singleRowIdxs.forEach((rowIdx) => {
                if (spreadsheet.rowIdxToRowMap.has("" + rowIdx)) {
                    rowIdxsToKeep.add(rowIdx);
                } else {
                    rowIdxsToFetch.add(rowIdx);
                }
            });

            let updateWithRows = (rowsFromServer: Row[]) => {
                let rowIdxToRowMap: d3.Map<Row> = d3.map<Row>();
                // populate rows from server
                rowsFromServer.forEach((row) => rowIdxToRowMap.set("" + row.idx, row));
                // populate rows from current memory
                rowIdxsToKeep.forEach((idx) => rowIdxToRowMap.set("" + idx, spreadsheet.rowIdxToRowMap.get("" + idx)))
                // replace idx to row map on spreadsheet obj
                spreadsheet.rowIdxToRowMap = rowIdxToRowMap;
                // use mainHeatmapIdxs to replace old filteredAndSortedRows
                spreadsheet.filteredAndSortedRows = mainHeatmapIdxs.map((idx) => {
                    return <NumericRow>rowIdxToRowMap.get("" + idx);
                });
            };

            let toFetchArr = Array.from(rowIdxsToFetch.values());
            if (toFetchArr.length > 0) {
                return this.getRowData(spreadsheet, toFetchArr).map(fetchedRows => {
                    updateWithRows(fetchedRows);
                    return fetchedRows.length;
                });
            } else {
                updateWithRows([]);
                return Observable.of(0);
            }
        } else {
            return Observable.of(0);
        }
    }
    
    /**
     * Given a job id, first fetches the spreadsheet ids, then use the id list to fetch spreadsheets from ssviz_spreadsheets endpoint
     */
    private getSpreadsheetsForJobId(jobId: number): Observable<Spreadsheet[]> {
        return this.getSpreadsheetIdsForJobId(jobId)
            .flatMap(spreadsheetIds => {
                let url: string = this._spreadsheetsUrl + '?id=' + spreadsheetIds.join();
                return this.authHttp
                    .get(url)
                    .map(res => {
                        return res.json()._items.map((ssItem: any) => {
                            return new Spreadsheet(
                                ssItem._id,
                                ssItem.file_id, 
                                ssItem.feature_names,
                                ssItem.feature_types,
                                [],  
                                [],  
                                ssItem.sample_names,
                                ssItem.is_file_samples_as_rows,
                                ssItem.feature_nan_counts,
                                ssItem.sample_nan_counts);
                        });
                    });
            });
    }

    /**
     * Given the job id for an SSV job, returns the associated spreadsheet ids.
     */
    private getSpreadsheetIdsForJobId(jobId: number): Observable<number[]> {
        let url: string = this._jobSpreadsheetsUrl + '?job_id=' + jobId;
        return this.authHttp
            .get(url)
            .map(res => {
                return res.json()._items.map((jobSpreadsheetDatum: any) => {
                    return jobSpreadsheetDatum.ssviz_spreadsheet_id;
                });
            });
    }

    /**
     * call the ssviz_feature_variances endpoint with list of spreadsheet ids, updating spreadsheets upon completion
     */
    private updateSpreadsheetsWithVariances(spreadsheets: Spreadsheet[]): Observable<Spreadsheet[]> {
        let ids = spreadsheets.map((spreadsheet: Spreadsheet) => spreadsheet.spreadsheetId);
        let url: string = this._rowVariancesUrl + "?ssviz_spreadsheet_id=" + ids.join();
        return this.authHttp
            .get(url)
            .map(res => {
                res.json()._items.forEach((variancesDatum: any) => {
                    let matches = spreadsheets.filter(ss => ss.spreadsheetId == variancesDatum.ssviz_spreadsheet_id);
                    if (matches.length == 1) {
                        matches[0].rowVariances = variancesDatum.scores;
                    } else {
                        this.logger.error("Got " + matches.length + " matches for " + variancesDatum.ssviz_spreadsheet_id);
                    }
                });
                return spreadsheets;
            });
    }

    /**
     * Given a spreadsheet id and a list of row indices within the spreadsheet,
     * fetches the row data for the indices.
     * TODO take a Spreadsheet instead? see how it feels as models and components settle down
     */
    private getRowData(spreadsheet: Spreadsheet, rowIdxs: number[]): Observable<Row[]> {
        // TODO experiment with chunk size
        return this.getRowDataChunks(spreadsheet, rowIdxs, 100).toArray();
    }

    private getRowDataChunks(spreadsheet: Spreadsheet, rowIdxs: number[], chunkSize: number, chunkIndex = 0): Observable<Row> {
        // TODO factor out this chunk logic, which also appears in at least the GSC service
        let sliceStart: number = chunkIndex * chunkSize;
        let sliceEnd: number = sliceStart + chunkSize;
        let nextChunkIndex: number = chunkIndex + 1;
        if (sliceEnd >= rowIdxs.length) {
            sliceEnd = rowIdxs.length;
            nextChunkIndex = null;
        }
        let rowIdxsChunk: number[] = rowIdxs.slice(sliceStart, sliceEnd);
        let url: string = this._rowDataUrl +
            '?ssviz_spreadsheet_id=' + spreadsheet.spreadsheetId + '&feature_idx=' + rowIdxsChunk.join();
        rowIdxsChunk = undefined;
        return EveUtilities
            .getAllItems(url, this.authHttp)
            .flatMap((rowData: any[]) => {
                let itemStream: Observable<Row> = Observable.from(rowData.map((item: any) => {
                    let returnVal: Row = null;
                    let rowType = spreadsheet.rowTypes[item.feature_idx];
                    if (rowType == "categoric") {
                        returnVal = new CategoricRow(item.values, item.feature_idx, spreadsheet);
                    } else if (rowType == "numeric") {
                        returnVal = new NumericRow(item.values, item.feature_idx, spreadsheet);
                    } else {
                        returnVal = new Row(item.values, item.feature_idx, spreadsheet);
                    }
                    return returnVal;
                }));
                if (nextChunkIndex !== null) {
                    itemStream = itemStream.concat(this.getRowDataChunks(spreadsheet, rowIdxs, chunkSize, nextChunkIndex));
                }
                return itemStream;
        });
    }

    /**
     * Gets pvalues for time-to-event analysis. Uses pvalues already in
     * memory if we have them or else fetches them
     * from the server.
     */
    private getTimeToEventPvals(stateRequest: SSVStateRequest): Observable<TimeToEventPvalue[]> {
        // get the pval requests
        let pvalRequests = stateRequest.timeToEventPvalRequests;
        // if there are no pval requests, early exist
        if (!pvalRequests || pvalRequests.length == 0) {
            return Observable.of([]);
        }
        // get the time-to-event analysis context
        let eventRR = stateRequest.timeToEventEventRowRequest;
        let timeRR = stateRequest.timeToEventTimeRowRequest;
        let eventVal = stateRequest.timeToEventEventValue;
        // if the context is incomplete, early exit
        if (!eventRR || !timeRR || !eventVal) {
            return Observable.of([]);
        }
        // ok, the context is complete
        // compare it with the last context
        let lastState = this._broadcast.getValue();
        let lastStateRequest = lastState.stateRequest;
        let contextChanged = !lastStateRequest ||
            !RowStateRequest.equal(lastStateRequest.timeToEventEventRowRequest, eventRR) ||
            !RowStateRequest.equal(lastStateRequest.timeToEventTimeRowRequest, timeRR) ||
            lastStateRequest.timeToEventEventValue != eventVal;
        if (contextChanged) {
            // fetch all
            let pvalStreams = pvalRequests.map((req) => {
                return this.getTimeToEventPval(timeRR, eventRR, eventVal, req);
            });
            return Observable.forkJoin(pvalStreams);
        }
        // context hasn't changed
        // determine whether any of the pvalRequests changed
        // note we're only interested in additions, not removals--for one thing,
        // removals aren't possible with the current UI
        let pvalStreams = pvalRequests.map((rsr) => {
            // if we already have this value, return an Observable.of it
            // otherwise, fetch the value from the server
            let match = lastState.timeToEventPvals.find((pvalObj) => {
                return RowStateRequest.equal(rsr, pvalObj.request);
            });
            if (match) {
                return Observable.of(match);
            }
            return this.getTimeToEventPval(timeRR, eventRR, eventVal, rsr);
        });
        return Observable.forkJoin(pvalStreams);
    }

    private getTimeToEventPval(
        timeRR: RowStateRequest, eventRR: RowStateRequest, eventVal: string,
        analysisRR: RowStateRequest): Observable<TimeToEventPvalue> {
        let url = this._survivalAnalysesUrl +
            "?duration_spreadsheet_id=" + timeRR.spreadsheetId +
            "&duration_feature_idx=" + timeRR.rowIdx +
            "&grouping_spreadsheet_id=" + analysisRR.spreadsheetId +
            "&grouping_feature_idx=" + analysisRR.rowIdx +
            "&event_spreadsheet_id=" + eventRR.spreadsheetId +
            "&event_feature_idx=" + eventRR.rowIdx +
            "&event_val=" + eventVal;
        return this.authHttp
            .get(url)
            .map(res => {
                return {request: analysisRR, pval: res.json().pval}
            });
    }
}
