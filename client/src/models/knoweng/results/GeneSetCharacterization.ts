export class ComparisonGeneSetSupercollection {
    constructor(
        public name: string,
        public collections: ComparisonGeneSetCollection[],
        public displayData: SupercollectionDisplayData) {
    }
    static fromComparisonGeneSets(geneSets: ComparisonGeneSet[]): ComparisonGeneSetSupercollection[] {
        let nestedData: any[] = d3.nest()
            .key((geneSet: ComparisonGeneSet) => geneSet.supercollectionName)
            .key((geneSet: ComparisonGeneSet) => geneSet.collectionName)
            .entries(geneSets);
        let supercollections: ComparisonGeneSetSupercollection[] = [];
        nestedData.forEach((supercollectionEntry: any) => {
            let supercollectionName: string = supercollectionEntry.key;
            let supercollectionValues: any[] = supercollectionEntry.values;
            let collections: ComparisonGeneSetCollection[] = [];
            supercollectionValues.forEach((collectionEntry: any) => {
                let collectionName: string = collectionEntry.key;
                let collectionGeneSets: ComparisonGeneSet[] = collectionEntry.values;
                collections.push(new ComparisonGeneSetCollection(collectionName, collectionGeneSets));
            });
            supercollections.push(new ComparisonGeneSetSupercollection(
                supercollectionName,
                collections,
                DISPLAY_DATA_REGISTRY[supercollectionName]));
        });
        return supercollections;
    }
}

export class SupercollectionDisplayData {
    constructor(
        public color: string,
        public icon: string,
        public displayOrder: number) {
    }
}

export var DISPLAY_DATA_REGISTRY: {[propertyName: string]: SupercollectionDisplayData} = {
    "Pathways": new SupercollectionDisplayData('#e79038', 'supercollection-pathways', 2),
    "Disease/Drug": new SupercollectionDisplayData('#1f977e', 'supercollection-disease-drug', 5),
    "Protein Domains": new SupercollectionDisplayData('#64a2d9', 'supercollection-protein-domains', 6),
    "Ontologies": new SupercollectionDisplayData('#e05869', 'supercollection-ontologies', 1),
    "Regulation": new SupercollectionDisplayData('#3dbfc2', 'supercollection-regulation', 4),
    "Tissue Expression": new SupercollectionDisplayData('#cacf47', 'supercollection-tissue-expression', 3),
    "My Gene Sets": new SupercollectionDisplayData('#29465f', 'supercollection-mine', 7)
}

export class ComparisonGeneSetCollection {
    constructor(
        public name: string,
        public sets: ComparisonGeneSet[]) {
    }
}

export class ComparisonGeneSet {
    constructor(
        public knId: string,
        public name: string,
        public speciesId: number,
        public geneCount: number,
        public url: string,
        public collectionName: string,
        public edgeTypeName: string,
        public supercollectionName: string) {
    }
}

export class UserGeneSet {
    constructor(
        public name: string,
        public geneIds: string[]) {
    }
}

export class ComparisonGeneSetScores {
    scoreMap: d3.Map<UserGeneSetScores> = d3.map<UserGeneSetScores>();
    constructor(
        public serverData: any) {
        // serverData: object in which property names are ComparisonGeneSet kn ids
        // and values are objects corresponding to UserGeneSetScores
        for (let prop in serverData) {
            if (serverData.hasOwnProperty(prop)) {
                this.scoreMap.set(prop, new UserGeneSetScores(serverData[prop]));
            }
        }
    }
    getMaxGeneSetLevelScore(filteredKnIds: string[], filteredUserGeneSetNames: string[]): number {
        let userGeneSetScores: UserGeneSetScores[] = filteredKnIds.map((knId: string) => this.scoreMap.get(knId));
        userGeneSetScores = userGeneSetScores.filter((ugss: UserGeneSetScores) => typeof ugss != 'undefined');
        return d3.max(userGeneSetScores, (ugss: UserGeneSetScores) => ugss.getMaxGeneSetLevelScore(filteredUserGeneSetNames));
    }
    getMinGeneSetLevelScore(filteredKnIds: string[], filteredUserGeneSetNames: string[]): number {
        let userGeneSetScores: UserGeneSetScores[] = filteredKnIds.map((knId: string) => this.scoreMap.get(knId));
        userGeneSetScores = userGeneSetScores.filter((ugss: UserGeneSetScores) => typeof ugss != 'undefined');
        return d3.min(userGeneSetScores, (ugss: UserGeneSetScores) => ugss.getMinGeneSetLevelScore(filteredUserGeneSetNames));
    }
    getMaxGeneSetLevelScoreForComparisonGeneSet(knId: string, filteredUserGeneSetNames: string[]): number {
        return this.scoreMap.get(knId).getMaxGeneSetLevelScore(filteredUserGeneSetNames);
    }
    getMaxGeneSetLevelScoreForUserGeneSet(filteredKnIds: string[], name: string): number {
        let userGeneSetScores: UserGeneSetScores[] = filteredKnIds.map((knId: string) => this.scoreMap.get(knId));
        userGeneSetScores = userGeneSetScores.filter((ugss: UserGeneSetScores) => typeof ugss != 'undefined');
        return d3.max(userGeneSetScores, (ugss: UserGeneSetScores) => {
            let returnVal: number = undefined;
            if (ugss.scoreMap.has(name)) {
                return ugss.scoreMap.get(name).shadingScore;
            }
            return returnVal;
        });
    }
}

export class UserGeneSetScores {
    scoreMap: d3.Map<GeneSetLevelScore> = d3.map<GeneSetLevelScore>();
    constructor(
        public serverData: any) {
        // serverData: object in which property names are UserGeneSet names and
        // values are objects corresponding to GeneSetLevelScores
        for (let prop in serverData) {
            if (serverData.hasOwnProperty(prop)) {
                let scores: any = serverData[prop];
                this.scoreMap.set(prop, new GeneSetLevelScore(
                    scores.shading_score, scores.overlap_count));
            }
        }
    }
    getMaxGeneSetLevelScore(filteredUserGeneSetNames: string[]): number {
        let geneSetLevelScores: GeneSetLevelScore[] = filteredUserGeneSetNames.map((ugsName: string) => this.scoreMap.get(ugsName));
        geneSetLevelScores = geneSetLevelScores.filter((gsls: GeneSetLevelScore) => typeof gsls != 'undefined');
        return d3.max(geneSetLevelScores, (gls: GeneSetLevelScore) => gls.shadingScore);
    }
    getMinGeneSetLevelScore(filteredUserGeneSetNames: string[]): number {
        let geneSetLevelScores: GeneSetLevelScore[] = filteredUserGeneSetNames.map((ugsName: string) => this.scoreMap.get(ugsName));
        geneSetLevelScores = geneSetLevelScores.filter((gsls: GeneSetLevelScore) => typeof gsls != 'undefined');
        return d3.min(geneSetLevelScores, (gls: GeneSetLevelScore) => gls.shadingScore);
    }
}

export class GeneSetLevelScore {
    constructor(
        public shadingScore: number,
        public overlapCount: number) {
    }
}

export class Result {
    constructor(
        public jobId: number,
        public userGeneSets: UserGeneSet[],
        public setLevelScores: ComparisonGeneSetScores,
        public minimumScore: number) {
    }
}
