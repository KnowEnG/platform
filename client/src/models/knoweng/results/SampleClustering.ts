export class TopGenes {
    scopeMap: d3.Map<TopGene[]> = d3.map<TopGene[]>();
    constructor(serverData: any) {
        // serverData: object in which property names are scope names and values
        // values are arrays of object literals containing id, name, and score
        for (let prop in serverData) {
            if (serverData.hasOwnProperty(prop)) {
                let vals = <any[]>serverData[prop];
                this.scopeMap.set(prop, vals.map((val) => new TopGene(val.id, val.name, val.score)));
            }
        }
    }
}

export class TopGene {
    constructor(
        public id: string,
        public name: string,
        public score: number) {
    }
}

export class Sample {
    constructor(
        public id: string,
        public cluster: number) {
    }
}

export class Cluster {
    public shortName: string;
    public longName: string;
    constructor(
            public index: number,
            public size: number) {
        this.shortName = "C" + (index+1);
        this.longName = "Cluster " + (index+1);
    }
}

export class PhenotypeData {
    constructor(
        public name: string,
        public score: number,
        public values: number[] | string[]) {
    }
}

export class Result {
    public clusters: Cluster[];
    
    
    constructor(
            public jobId: number,
            public topGenes: TopGenes,
            public samples: Sample[],
            public genesHeatmap: number[][],
            public samplesHeatmap: number[][],
            public phenotypes: PhenotypeData[]) {
        // create an array of k:v pairs in which k=cluster index (as a string)
        // and v=size of cluster
        let clusterIndexToSize = d3.nest<Sample>()
            .key((sample: Sample) => ""+sample.cluster) // must be a string
            .rollup((leaves: Sample[]) => leaves.length)
            .entries(samples);
        // convert to Cluster[]
        clusterIndexToSize.sort((a: {key: string; values: number}, b: {key: string, values: number}) => {
            return d3.ascending(+a.key, +b.key);
        });
        this.clusters = clusterIndexToSize.map((kvp: {key: string; values: number}) => {
            return new Cluster(+kvp.key, kvp.values);
        });
    }
}
