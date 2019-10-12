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

    /** for "convenience" until we have a stronger link between eve schema and client pipeline config */
    /** not used yet
    logPipelineSchemas(): void {
        PIPELINES.forEach((pipeline: Pipeline) => {
            let nameSchemaMap: d3.Map<any> = d3.map<any>();
            nameSchemaMap.set("type", "string");
            nameSchemaMap.set("required", true);

            let projectSchemaMap: d3.Map<any> = d3.map<any>();
            projectSchemaMap.set("type", "objectid");
            projectSchemaMap.set("required", true);
            var projectRelationMap: d3.Map<any> = d3.map<any>();
            projectRelationMap.set("resource", "projects");
            projectRelationMap.set("field", "_id");
            projectRelationMap.set("embeddable", true);
            projectSchemaMap.set("data_relation", projectRelationMap);

            let notesSchemaMap: d3.Map<any> = d3.map<any>();
            notesSchemaMap.set("type", "string");
            notesSchemaMap.set("required", false);

            let statusSchemaMap: d3.Map<any> = d3.map<any>();
            statusSchemaMap.set("type", "string");
            statusSchemaMap.set("required", true);
            statusSchemaMap.set("default", "running");
            statusSchemaMap.set("allowed", ["running", "completed", "failed"]);

            let entries: SchemaEntry[] = [
                new SchemaEntry("name", nameSchemaMap),
                new SchemaEntry("project", projectSchemaMap),
                // TODO add tags
                new SchemaEntry("notes", notesSchemaMap),
                new SchemaEntry("status", statusSchemaMap),
            ];

            let form: Form = pipeline.getForm();
            if (form !== null) {
                entries = entries.concat(form.getSchemaEntries());
            }
            // TODO collapse on name collisions (as happens, e.g., with hidden fields enabled/disabled according to context)
            // TODO get the whole thing working in eve; documentation on "oneof" and "anyof" isn't great
            entries.forEach((entry: SchemaEntry) => {
                // FIXME: Need to figure out how to inject LogService here, or refactor this to be a proper class
                console.log(SchemaEntry.levelToString(entry.dbName, entry.definition, 1));
            });
        });
    }
    */
}
