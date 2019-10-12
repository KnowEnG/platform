export class Result {

    constructor(
            public jobId: number,
            public consensusMatrixLabels: string[],
            public consensusMatrixValues: number[][],
            public consensusMatrixFileId: number,
            public initialColumnGroupingFileId: number,
            public initialColumnGroupingFeatureIndex: number,
            public initialColumnSortingFileId: number,
            public initialColumnSortingFeatureIndex: number,
            public globalSilhouetteScore: number,
            public clusterSilhouetteScores: number[]) { }
}
