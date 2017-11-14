import {NgModule, Component, OnInit, ErrorHandler} from '@angular/core';
import {CommonModule}   from '@angular/common';

import {MmbdbRoutingModule} from './MmbdbRoutingModule';
import {NestCommonModule} from '../common/NestCommonModule';

import {MmbdbComponent} from './MmbdbComponent';
import {AbundanceBarChart} from './AbundanceBarChart';
import {AbundanceFormatter} from '../../pipes/mmbdb/AbundanceFormatter';
import {AbundanceSlider} from './AbundanceSlider';
import {AbundanceTable} from './AbundanceTable';
import {AbundanceTopOTU} from './AbundanceTopOTU';
import {AlphaDiversityComponent} from './AlphaDiversityComponent';
import {BuildComparisonComponent} from './BuildComparisonComponent';
import {CohortComparisonTool} from './CohortComparisonTool';
import {CohortPlaceholder} from './CohortPlaceholder';
import {CreateReportsComponent} from './CreateReportsComponent';
import {DifferenceBarChart} from './DifferenceBarChart';
import {DiscoverCohortsComponent} from './DiscoverCohortsComponent';
import {EvennessTable} from './EvennessTable';
import {GettingStartedComponent} from './GettingStartedComponent';
import {GroupedBarChart} from './GroupedBarChart';
import {IndividualPlaceholder} from './IndividualPlaceholder';
import {RadarChart} from './RadarChart';
import {RelativeAbundanceComponent} from './RelativeAbundanceComponent';
import {RichnessTable} from './RichnessTable';
import {TopOTUPicker} from './TopOTUPicker';
import {TreeDetailTable} from './TreeDetailTable';
import {TreeExplorer} from './TreeExplorer';

import {NestErrorHandler} from '../../services/common/NestErrorHandler';

@NgModule({
    imports: [
        CommonModule,
        MmbdbRoutingModule,
        NestCommonModule
    ],
    declarations: [
        MmbdbComponent,
        AbundanceBarChart, 
        AbundanceFormatter,
        AbundanceSlider, 
        AbundanceTable, 
        AbundanceTopOTU,
        AlphaDiversityComponent,
        BuildComparisonComponent,
        CohortComparisonTool,
        CohortPlaceholder,
        CreateReportsComponent,
        DifferenceBarChart,
        DiscoverCohortsComponent,
        EvennessTable,
        GettingStartedComponent,
        GroupedBarChart,
        IndividualPlaceholder,
        RadarChart,
        RelativeAbundanceComponent,
        RichnessTable,
        TopOTUPicker,
        TreeDetailTable,
        TreeExplorer
    ],
    providers: [
        {provide: ErrorHandler, useClass: NestErrorHandler},
    ]
})

export class MmbdbModule {}
