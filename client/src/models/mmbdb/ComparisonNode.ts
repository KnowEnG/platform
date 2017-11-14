/** This class represents items from ComparisonNodeService. */
export class ComparisonNode {
    constructor(
        public id: string,
        public name: string,
        public level: string,
        public comparisonId: string,
        public nodeIdx: string,
        public parentNodeIdx: string,
        public topOtus: number[]) {
    }
    /** Given a top OTU threshold, returns the number found in this node. */
    getNumTopOtus(topOtuThreshold: number) {
        // pgroves: "if you scan until you find one bigger than or equal to the
        // slider-value, whatever *index* you are at is the number for the red
        // circle"
        var index: number = -1;
        for (var i: number = 0; i < this.topOtus.length; i++) {
            if (this.topOtus[i] >= topOtuThreshold) {
                index = i;
                break;
            }
        }
        return index;
    }
}
