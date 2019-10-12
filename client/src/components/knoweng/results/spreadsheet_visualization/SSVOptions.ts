export class MainHeatmapGradientScale {
    constructor(
        public min: number, 
        public max: number,
        public gradientScale: any
    ) {}
}

export class ExpandedGroup {
    constructor(
        public groupPosition: number,
        public groupName: string,
        public groupStartColumnPos: number,
        public groupEndColumnPos: number
    ) {}
}

/**
 * A model for the first and last displayed column index (inclusive) in heatmaps.
 **/
export class ColumnIndices {
    constructor(
        public startPos: number, 
        public endPos: number,
        public totalColumnCount: number
    ) {}
    isShowingAll(): boolean {
        return this.startPos == 0 && (this.endPos + 1) == this.totalColumnCount; 
    }
    static equal(one: ColumnIndices, two: ColumnIndices): boolean {
        if (one && two) {
            return one.startPos == two.startPos && one.endPos == two.endPos;
        }
        return one == two; // both null/undefined
    }
}
