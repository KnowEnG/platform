export class SignatureScores {
    scoreMap: d3.Map<SampleScores> = d3.map<SampleScores>();
    constructor(
        serverData: any) {
        // serverData: object in which property names are signature ids
        // and values are objects corresponding to SampleScores
        for (let prop in serverData) {
            if (serverData.hasOwnProperty(prop)) {
                this.scoreMap.set(prop, new SampleScores(serverData[prop]));
            }
        }
    }
    getMaxScoreForSignature(signature: string, filteredSampleIds: string[]): number {
        return this.scoreMap.get(signature).getMaxScore(filteredSampleIds);
    }
    getMaxScoreForSample(filteredSignatureIds: string[], name: string): number {
        let sampleScores: SampleScores[] = filteredSignatureIds.map((signature) => this.scoreMap.get(signature));
        sampleScores = sampleScores.filter((ss: SampleScores) => typeof ss != 'undefined');
        return d3.max(sampleScores, (ss: SampleScores) => {
            let returnVal: number = undefined;
            if (ss.scoreMap.has(name)) {
                return ss.scoreMap.get(name);
            }
            return returnVal;
        });
    }
}

export class SampleScores {
    scoreMap: d3.Map<number> = d3.map<number>();
    orderedSampleIds: string[];
    constructor(
        serverData: any) {
        // serverData: object in which property names are sample ids and
        // values are scores
        for (let prop in serverData) {
            if (serverData.hasOwnProperty(prop)) {
                this.scoreMap.set(prop, serverData[prop]);
            }
        }
        this.orderedSampleIds = this.scoreMap.keys().sort((a: string, b: string) => {
            return d3.descending(this.scoreMap.get(a), this.scoreMap.get(b));
        });
    }
    getMaxScore(filteredSampleIds: string[]): number {
        return d3.max(filteredSampleIds.map((id) => this.scoreMap.get(id)));
    }
}

export class Result {
    constructor(
        public jobId: number,
        public scores: SignatureScores) {
    }
    getNumberOfSamples(): number {
        let returnVal = null;
        let sampleScores = this.scores.scoreMap.values();
        if (sampleScores.length > 0) {
            returnVal = sampleScores[0].orderedSampleIds.length;
        }
        return returnVal;
    }
}
