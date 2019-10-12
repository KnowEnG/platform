export class ResponseScores {
    scoreMap: d3.Map<FeatureScores> = d3.map<FeatureScores>();
    constructor(
        serverData: any) {
        // serverData: object in which property names are response names
        // and values are objects corresponding to FeatureScores
        for (let prop in serverData) {
            if (serverData.hasOwnProperty(prop)) {
                this.scoreMap.set(prop, new FeatureScores(serverData[prop]));
            }
        }
    }
    getMaxScoreForResponse(response: string, filteredFeatureIds: string[]): number {
        return this.scoreMap.get(response).getMaxScore(filteredFeatureIds);
    }
    getMaxScoreForFeature(filteredResponseNames: string[], name: string): number {
        let featureScores: FeatureScores[] = filteredResponseNames.map((response) => this.scoreMap.get(response));
        featureScores = featureScores.filter((fs: FeatureScores) => typeof fs != 'undefined');
        return d3.max(featureScores, (fs: FeatureScores) => {
            let returnVal: number = undefined;
            if (fs.scoreMap.has(name)) {
                return fs.scoreMap.get(name);
            }
            return returnVal;
        });
    }
}

export class FeatureScores {
    scoreMap: d3.Map<number> = d3.map<number>();
    orderedFeatureIds: string[];
    constructor(
        serverData: any) {
        // serverData: object in which property names are feature ids and
        // values are scores
        for (let prop in serverData) {
            if (serverData.hasOwnProperty(prop)) {
                this.scoreMap.set(prop, serverData[prop]);
            }
        }
        this.orderedFeatureIds = this.scoreMap.keys().sort((a: string, b: string) => {
            return d3.descending(this.scoreMap.get(a), this.scoreMap.get(b));
        });
    }
    getMaxScore(filteredFeatureIds: string[]): number {
        return d3.max(filteredFeatureIds.map((id) => this.scoreMap.get(id)));
    }
}

export class Result {
    public featureIdToNameMap: d3.Map<string> = d3.map<string>();
    constructor(
        public jobId: number,
        public scores: ResponseScores,
        public minimumScore: number,
        featureIdToNameMapServerData: any ) {
        // featureIdToNameMapServerData: object in which property names are
        // feature ids and values are feature names
        for (let prop in featureIdToNameMapServerData) {
            if (featureIdToNameMapServerData.hasOwnProperty(prop)) {
                this.featureIdToNameMap.set(prop, featureIdToNameMapServerData[prop]);
            }
        }
    }
}
