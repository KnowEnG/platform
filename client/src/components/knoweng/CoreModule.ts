import {ModuleWithProviders, NgModule, Optional, SkipSelf} from '@angular/core';

import {CommonModule} from '@angular/common';

import {FeaturePrioritizationService} from '../../services/knoweng/FeaturePrioritizationService';
import {FileService} from '../../services/knoweng/FileService';
import {GeneSetCharacterizationService} from '../../services/knoweng/GeneSetCharacterizationService';
import {JobService} from '../../services/knoweng/JobService';
import {ProjectService} from '../../services/knoweng/ProjectService';
import {KnowledgeNetworkService} from '../../services/knoweng/KnowledgeNetworkService';
import {PipelineService} from '../../services/knoweng/PipelineService';
import {SampleClusteringService} from '../../services/knoweng/SampleClusteringService';
import {SignatureAnalysisService} from '../../services/knoweng/SignatureAnalysisService';
import {SpreadsheetVisualizationService} from '../../services/knoweng/SpreadsheetVisualizationService';
import {SessionService} from '../../services/common/SessionService';

@NgModule({
    imports: [CommonModule],
    providers: [
        FeaturePrioritizationService,
        FileService,
        GeneSetCharacterizationService,
        JobService,
        ProjectService,
        KnowledgeNetworkService,
        PipelineService,
        SampleClusteringService,
        SignatureAnalysisService,
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
