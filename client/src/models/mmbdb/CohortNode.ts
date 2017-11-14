/** This class represents items from CohortNodeService. */
export class CohortNode {
    [key: string]: any; // allow access to fields using cohortNode[key] (e.g., cohortNode['parentNodeIdx'])
    constructor(
        public id: string,
        public name: string,
        public level: string,
        public cohortId: string,
        public nodeIdx: string,
        public parentNodeIdx: string,
        public relativeAbundanceMean: number,
        public relativeAbundanceQuantiles: number[],
        public relativeAbundanceHistoNumZeros: number,
        public relativeAbundanceHistoBinStartX: number[],
        public relativeAbundanceHistoBinEndX: number[],
        public relativeAbundanceHistoBinHeightY: number[],
        public numUniqueOtusMean: number,
        public numUniqueOtusDensityPlotX: number[],
        public numUniqueOtusDensityPlotY: number[],
        public numUniqueOtusHistoNumZeros: number,
        public numUniqueOtusHistoBinStartX: number[],
        public numUniqueOtusHistoBinEndX: number[],
        public numUniqueOtusHistoBinHeightY: number[],
        public normalizedEntropyMean: number,
        public normalizedEntropyHistoNumZeros: number,
        public normalizedEntropyHistoBinStartX: number[],
        public normalizedEntropyHistoBinEndX: number[],
        public normalizedEntropyHistoBinHeightY: number[]) {
    }
}
