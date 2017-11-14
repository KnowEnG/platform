export class ResponseScores {
    scoreMap: d3.Map<GeneScores> = d3.map<GeneScores>();
    constructor(
        serverData: any) {
        // serverData: object in which property names are response names
        // and values are objects corresponding to GeneScores
        for (let prop in serverData) {
            if (serverData.hasOwnProperty(prop)) {
                this.scoreMap.set(prop, new GeneScores(serverData[prop]));
            }
        }
    }
    getMaxScoreForResponse(response: string, filteredGeneIds: string[]): number {
        return this.scoreMap.get(response).getMaxScore(filteredGeneIds);
    }
    getMaxScoreForGene(filteredResponseNames: string[], name: string): number {
        let geneScores: GeneScores[] = filteredResponseNames.map((response) => this.scoreMap.get(response));
        geneScores = geneScores.filter((gs: GeneScores) => typeof gs != 'undefined');
        return d3.max(geneScores, (gs: GeneScores) => {
            let returnVal: number = undefined;
            if (gs.scoreMap.has(name)) {
                return gs.scoreMap.get(name);
            }
            return returnVal;
        });
    }
}

export class GeneScores {
    scoreMap: d3.Map<number> = d3.map<number>();
    orderedGeneIds: string[];
    constructor(
        serverData: any) {
        // serverData: object in which property names are gene ids and
        // values are scores
        for (let prop in serverData) {
            if (serverData.hasOwnProperty(prop)) {
                this.scoreMap.set(prop, serverData[prop]);
            }
        }
        this.orderedGeneIds = this.scoreMap.keys().sort((a: string, b: string) => {
            return d3.descending(this.scoreMap.get(a), this.scoreMap.get(b));
        });
    }
    getMaxScore(filteredGeneIds: string[]): number {
        return d3.max(filteredGeneIds.map((id) => this.scoreMap.get(id)));
    }
}

export class Result {
    public geneIdToNameMap: d3.Map<string> = d3.map<string>();
    constructor(
        public jobId: number,
        public scores: ResponseScores,
        public minimumScore: number,
        geneIdToNameMapServerData: any ) {
        // geneIdToNameMapServerData: object in which property names are
        // gene ids and values are gene names
        for (let prop in geneIdToNameMapServerData) {
            if (geneIdToNameMapServerData.hasOwnProperty(prop)) {
                this.geneIdToNameMap.set(prop, geneIdToNameMapServerData[prop]);
            }
        }
    }
}
