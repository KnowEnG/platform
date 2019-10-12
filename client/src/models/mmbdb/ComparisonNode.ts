/** This class represents items from ComparisonNodeService. */
export class ComparisonNode {
    constructor(
        public id: number,
        public name: string,
        public level: string,
        public comparisonId: number,
        public nodeIdx: string,
        public parentNodeIdx: string,
        public topOtus: number[]) {
    }
    /** Given a top OTU threshold, returns the number found in this node. */
    getNumTopOtus(topOtuThreshold: number) {
        // if you scan until you find one bigger than or equal to the
        // slider-value, whatever *index* you are at is the number for the red
        // circle.
        // Edge cases:
        // 1. Empty list of topOtus. Always want index=0, so length of topOtus works
        // 2. 'number' is less than the first topOtu. Will hit index=0 and stop
        // 3. 'number' is greater than the last topOtu. Will never match and return the 
        //    length of topOtus, which means the count of all of them
        var index: number = this.topOtus.length;
        for (var i: number = 0; i < this.topOtus.length; i++) {
            if (this.topOtus[i] >= topOtuThreshold) {
                index = i;
                break;
            }
        }
        return index;
    }
}
