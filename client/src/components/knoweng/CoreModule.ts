import {ModuleWithProviders, NgModule, Optional, SkipSelf} from '@angular/core';

import {CommonModule} from '@angular/common';

import {FileService} from '../../services/knoweng/FileService';
import {GenePrioritizationService} from '../../services/knoweng/GenePrioritizationService';
import {GeneSetCharacterizationService} from '../../services/knoweng/GeneSetCharacterizationService';
import {JobService} from '../../services/knoweng/JobService';
import {ProjectService} from '../../services/knoweng/ProjectService';
import {KnowledgeNetworkService} from '../../services/knoweng/KnowledgeNetworkService';
import {PipelineService} from '../../services/knoweng/PipelineService';
import {SampleClusteringService} from '../../services/knoweng/SampleClusteringService';
import {SpreadsheetVisualizationService} from '../../services/knoweng/SpreadsheetVisualizationService';
import {SessionService} from '../../services/common/SessionService';

@NgModule({
    imports: [CommonModule],
    providers: [
        FileService,
        GenePrioritizationService,
        GeneSetCharacterizationService,
        JobService,
        ProjectService,
        KnowledgeNetworkService,
        PipelineService,
        SampleClusteringService,
        SpreadsheetVisualizationService,
        SessionService
    ]
})

export class CoreModule {
    constructor (@Optional() @SkipSelf() parentModule: CoreModule) {
        if (parentModule) {
            throw new Error('CoreModule is already loaded. Import it in the AppModule only');
        }
    }
}
