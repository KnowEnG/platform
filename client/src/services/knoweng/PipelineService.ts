import {Injectable} from '@angular/core';
import {Observable} from 'rxjs/Observable';
import {Subscription} from 'rxjs/Subscription';
import 'rxjs/add/operator/first';
import 'rxjs/add/operator/share';

import {Pipeline} from '../../models/knoweng/Pipeline';
import {AnalysisNetwork, Collection, Species} from '../../models/knoweng/KnowledgeNetwork';
import {FileService} from './FileService';
import {JobService} from './JobService';
import {KnowledgeNetworkService} from './KnowledgeNetworkService';
import {SampleClusteringPipeline} from '../../models/knoweng/pipelines/SampleClustering';
import {FeaturePrioritizationPipeline} from '../../models/knoweng/pipelines/FeaturePrioritization';
import {GeneSetCharacterizationPipeline} from '../../models/knoweng/pipelines/GeneSetCharacterization';
import {SignatureAnalysisPipeline} from '../../models/knoweng/pipelines/SignatureAnalysis';
import {SpreadsheetVisualizationPipeline} from '../../models/knoweng/pipelines/SpreadsheetVisualization';

@Injectable()
export class PipelineService {

    private pipelines: Pipeline[] = [];

    private speciesSub: Subscription;
    private collectionsSub: Subscription;
    private networksSub: Subscription;

    constructor(
            private knService: KnowledgeNetworkService,
            private fileService: FileService,
            private jobService: JobService) {

        // need to call first() on speciesStream because it's not a one-off http call--it's a persistent Observable in the service
        // need to call share() on everything so each pipeline can subscribe
        let speciesStream = this.knService.getSpecies().first((s: Species[]) => s.length > 0).share();
        let collectionsStream = this.knService.getCollections(null).share();
        let networksStream = this.knService.getAnalysisNetworks(null).share();

        this.pipelines = [
            new SampleClusteringPipeline(fileService, jobService, speciesStream, networksStream),
            new FeaturePrioritizationPipeline(fileService, jobService, speciesStream, networksStream),
            new GeneSetCharacterizationPipeline(fileService, jobService, speciesStream, collectionsStream, networksStream),
            new SignatureAnalysisPipeline(fileService, jobService),
            new SpreadsheetVisualizationPipeline(fileService, jobService)
        ];
    }

    getPipelines(): Pipeline[] {
        return this.pipelines;
    }

    getPipelineBySlug(slug: string): Pipeline {
        return this.pipelines.find((pipeline) => pipeline.slug === slug);
    }
}
