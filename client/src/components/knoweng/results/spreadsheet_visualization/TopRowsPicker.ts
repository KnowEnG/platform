import {Component, OnChanges, OnDestroy, Input, Output, EventEmitter} from '@angular/core';
import {Router} from '@angular/router';
import {Subscription} from 'rxjs/Subscription';

import {Spreadsheet, FilterType} from '../../../../models/knoweng/results/SpreadsheetVisualization';

@Component({
    moduleId: module.id,
    selector: 'top-rows-picker',
    templateUrl: './TopRowsPicker.html',
    styleUrls: ['./TopRowsPicker.css']
})
export class TopRowsPicker implements OnChanges, OnDestroy {
    class = 'relative';

    @Input()
    spreadsheet: Spreadsheet;

    @Input()
    scales: number[];

    @Input()
    topRowsCount: number;

    @Input()
    filterBy: FilterType;

    @Output()
    closeMe = new EventEmitter<SpreadsheetTopRowsThreshold>();

    sortedScores = [] as number[];

    currentScale = 0;

    inputHasError = false;

    constructor() {
    }

    ngOnChanges() {
        this.updateCurrentScale();
        this.sortScores();
    }

    ngOnDestroy() {
        this.closeMe.emit({spreadsheetId: this.spreadsheet.spreadsheetId, topRowsThreshold: this.topRowsCount});
    }

    updateCurrentScale(): void {
        this.currentScale = this.scales.find(scale => scale >= this.topRowsCount);
    }

    updateRowCount(selectedRowCount: number) {
        this.topRowsCount = selectedRowCount;
    }

    onTopRowsCountChanged(newVal: string) {
        // convert newVal to int
        // remember parseInt only returns NaN if the first non-whitespace character
        // can't be parsed as a number, so supplement that check with a regex
        let parsed = /^\s*\d+\s*$/.test(newVal) ? parseInt(newVal, 10) : NaN;
        if (!isNaN(parsed) && parsed > 0 && parsed <= this.sortedScores.length) {
            this.topRowsCount = parsed;
            // only update scale if new choice exceeds current scale
            if (this.topRowsCount > this.currentScale) {
                this.updateCurrentScale();
            }
            this.inputHasError = false;
        } else {
            this.inputHasError = true;
        }
    }

    sortScores(): void {
        let type: FilterType = this.filterBy;
        if (type == FilterType.VARIANCE) {
            // IMPORTANT: do not modifiy original rowVariances--using slice() to copy
            this.sortedScores = this.spreadsheet.rowVariances.slice().sort(function(a, b) {return b-a;});
        } else if (type == FilterType.CORRELATION_TO_GROUP) {
            // IMPORTANT: do not modifiy original rowCorrelations--using slice() to copy
            this.sortedScores = this.spreadsheet.rowCorrelations.slice().sort(function(a, b) {return b-a;});
        } else if (type == FilterType.SPREADSHEET_ORDER) {
            // IMPORTANT: do not modifiy original rowOriginalRanks--using slice() to copy
            this.sortedScores = this.spreadsheet.rowOriginalRanks.slice().sort(function(a, b) {return b-a;});
        }
        else {
            this.sortedScores = [];
        }
    }
}

export interface SpreadsheetTopRowsThreshold {
    spreadsheetId: number;
    topRowsThreshold: number;
}