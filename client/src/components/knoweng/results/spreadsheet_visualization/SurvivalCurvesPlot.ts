import {Component, OnChanges, SimpleChange, Input} from '@angular/core';

@Component({
    moduleId: module.id,
    selector: 'survival-curves-plot',
    templateUrl: './SurvivalCurvesPlot.html',
    styleUrls: ['./SurvivalCurvesPlot.css'],
})

// possible enhancements:
// add confidence smears (see _bounds: https://github.com/CamDavidsonPilon/lifelines/blob/master/lifelines/fitters/kaplan_meier_fitter.py)
// support second entry type in which we have start and end times instead of serial times
export class SurvivalCurvesPlot implements OnChanges {
    class = 'relative';

    @Input()
    timeUnitsLabel: string; // not used for now

    @Input()
    survivalCohorts: SurvivalCohort[];

    @Input()
    pValue: number;

    survivalCohortDisplayData: SurvivalCohortDisplayDatum[];

    plotAreaWidth = 601;
    plotAreaHeight = 431;

    margin = {
        top: 10,
        right: 5,
        bottom: 52,
        left: 125
    };

    padding = {
        top: 14,
        right: 16,
        bottom: 12,
        left: 16
    }

    axisLabelMargin = 37;
    numXAxisTicks = 14;
    numYAxisTicks = 11;
    xAxisTicks: {value: number, position: number}[] = [];
    yAxisTicks: {value: number, position: number}[] = [];
    axisTickHeight = 8;

    censorTickHeight = 10;

    constructor() {
    }
    ngOnChanges(changes: {[propertyName: string]: SimpleChange}) {
        if (this.survivalCohorts) {
            this.calculateLayout();
        } else {
            this.survivalCohortDisplayData = [];
        }
    }
    calculateLayout(): void {
        // create scales
        let maxTime = d3.max(this.survivalCohorts, (sc) => {
            return d3.max(sc.observations, (o) => o.serialTime);
        });
        let xScale = d3.scale.linear()
            .domain([0, maxTime])
            .range([0, this.plotAreaWidth])
            .nice(this.numXAxisTicks);
        this.xAxisTicks = xScale.ticks(this.numXAxisTicks).map((val) => {
            return {value: val, position: xScale(val)};
        });
        let yScale = d3.scale.linear()
            .domain([0, 1])
            .range([this.plotAreaHeight, 0]);
        this.yAxisTicks = yScale.ticks(this.numYAxisTicks).map((val) => {
            return {value: val, position: yScale(val)};
        });

        // determine curve and ticks for each cohort
        this.survivalCohortDisplayData = this.survivalCohorts.map((sc) => {
            let obs = sc.observations;
            let eventObservations = obs.filter((o) => o.isEvent);
            let censoredObservations = obs.filter((o) => !o.isEvent);
            // determine unique times associated with events
            let eventTimesSet = new Set<number>(eventObservations.map((o) => o.serialTime));
            let eventTimes = Array.from(eventTimesSet.values()).sort(d3.ascending);
            // calculate stats for each time
            let kmValues = eventTimes.map((t_i, index) => {
                // d_i is number of events occurring at time t_i (not cumulative events)
                let d_i = obs.filter((o) => o.isEvent && o.serialTime == t_i).length;
                // Y_i is number at risk at time t_i
                let Y_i = obs.filter((o) => o.serialTime > t_i).length;
                let s_t = Y_i == 0 ? 0 : 1 - (d_i/Y_i);
                return {t_i, d_i, Y_i, s_t, S_t: null};
            });
            // calculate running stats
            kmValues.forEach((kmv, index) => {
                let last_S_t = index == 0 ? 1 : kmValues[index-1].S_t;
                kmv.S_t = last_S_t * kmv.s_t;
            });
            // need to handle four cases:
            // 1. 0 events, 0 censored: no path, no points
            // 2. 0 events, >0 censored: horizontal path, points on that path
            // 3. >0 events, 0 censored: path, no points
            // 4. >0 events, >0 censored: path, points
            let path = "";
            let censorPoints: {x: number, y: number}[] = [];
            if (eventObservations.length > 0) {
                // make sure path begins at top-left corner
                let points: [number, number][] = [[xScale(0), yScale(1)]];
                // mapping kmValues to [number, number][] to avoid typings
                // problem seen when passing kmValues to a line generator
                // configured with x and y accessors
                kmValues.forEach((kmv) => {
                    points.push([xScale(kmv.t_i), yScale(kmv.S_t)] as [number, number])
                });
                path = d3.svg.line().interpolate('step-after')(points);
                let probabilityScale = d3.scale.threshold<number>()
                    .domain(kmValues.map((kmv) => kmv.t_i))
                    .range([1].concat(kmValues.map((kmv) => kmv.S_t)));
                censorPoints = censoredObservations.map((o) => {
                    return {x: xScale(o.serialTime), y: yScale(probabilityScale(o.serialTime))};
                });
                // if the maximum serial time associated with a censor point is
                // greater than the maximum serial time associated with an event,
                // we need to extend the path
                let maxEventTime = eventTimes[eventTimes.length-1];
                let maxCensorTime = d3.max(censoredObservations, (o) => o.serialTime);
                if (maxCensorTime && maxCensorTime > maxEventTime) {
                    path += "H" + xScale(maxCensorTime) + "V" + yScale(probabilityScale(maxCensorTime));
                }
            } else if (eventObservations.length == 0 && censoredObservations.length > 0) {
                // path is horizontal line at height 1 extending from time 0 to the
                // max serial time
                let maxSerialTime = d3.max(censoredObservations, (o) => o.serialTime);
                path = d3.svg.line()([[xScale(0), yScale(1)], [xScale(maxSerialTime), yScale(1)]]);
                // censor points are all at height 1
                censorPoints = censoredObservations.map((o) => {
                    return {x: xScale(o.serialTime), y: yScale(1)};
                });
            }
            return new SurvivalCohortDisplayDatum(sc, path, censorPoints);
        });
    }
    getSvgWidth(): number {
        return this.plotAreaWidth + this.margin.left + this.margin.right +
            this.padding.left + this.padding.right;
    }
    getSvgHeight(): number {
        return this.plotAreaHeight + this.margin.top + this.margin.bottom +
            this.padding.top + this.padding.bottom;
    }
    getBorderTopLeftX(): number {
        return this.margin.left;
    }
    getBorderTopLeftY(): number {
        return this.margin.top;
    }
    getBorderBottomRightX(): number {
        return this.getBorderTopLeftX() + this.plotAreaWidth + this.padding.left +
            this.padding.right;
    }
    getBorderBottomRightY(): number {
        return this.getBorderTopLeftY() + this.plotAreaHeight + this.padding.top + 
            this.padding.bottom;
    }
}

export class SurvivalCohort {
    constructor(
        public label: string,
        public color: string,
        public observations: SurvivalObservation[]) {
    }
}

export class SurvivalObservation {
    constructor(
        /**
         * serial time: time elapsed between enrollment/start of observation
         * and event/censor.
         */
        public serialTime: number,
        /**
         * true if the observation ended with the event of interest, else
         * false (censored, meaning no event at this time and no knowledge of
         * event beyond this time).
         */
        public isEvent: boolean) {
            if (serialTime === undefined || serialTime === null) {
                throw "Serial time must be a number.";
            }
            if (isEvent === undefined || isEvent === null) {
                this.isEvent = false;
            }
    }
}

class SurvivalCohortDisplayDatum {
    constructor(
        public cohort: SurvivalCohort,
        public path: string,
        public censorPoints: {x: number, y: number}[]) {
    }
}
