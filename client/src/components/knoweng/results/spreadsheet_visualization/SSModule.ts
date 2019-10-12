import {NgModule} from '@angular/core';
import {CommonModule} from '@angular/common';
import {FormsModule} from '@angular/forms';
import { AngularDraggableModule } from 'angular2-draggable';
import {BsDropdownModule, TooltipModule, PopoverModule, TypeaheadModule} from 'ngx-bootstrap';

import {NestCommonModule} from '../../../common/NestCommonModule';
import {ResultsCommonModule} from '../common/ResultsCommonModule';
import {DataArea} from './DataArea';
import {HeatmapPane} from './HeatmapPane';
import {MiniDistributionGraph} from './MiniDistributionGraph';
import {PrimaryVisualization} from './PrimaryVisualization';
import {ThresholdSlider} from './ThresholdSlider';
import {RowSelector} from './RowSelector';
import {SecondaryVisualization} from './SecondaryVisualization';
import {SingleRowHeatmap} from './SingleRowHeatmap';
import {SSVisualization} from './SSVisualization';
import {SurvivalCurvesPlot} from './SurvivalCurvesPlot';
import {TopRowsPicker} from './TopRowsPicker';
import {ColumnOptionsComponent} from './ColumnOptionsComponent';
import {TopOptionsComponent} from './TopOptionsComponent';

import {NumberFormatPipe} from '../../../../pipes/knoweng/NumberFormatPipe';

@NgModule({
    imports: [
        CommonModule,
        FormsModule,
        BsDropdownModule.forRoot(),
        TypeaheadModule.forRoot(),
        AngularDraggableModule,
        NestCommonModule,
        ResultsCommonModule,
        PopoverModule,
        TooltipModule
    ],
    declarations: [
        DataArea,
        HeatmapPane,
        MiniDistributionGraph,
        PrimaryVisualization,
        ThresholdSlider,
        RowSelector,
        SecondaryVisualization,
        SingleRowHeatmap,
        SSVisualization,
        SurvivalCurvesPlot,
        TopRowsPicker,
        ColumnOptionsComponent,
        TopOptionsComponent
    ],
    exports: [
        // DataArea, -- SC defines its own,
        HeatmapPane,
        MiniDistributionGraph,
        PrimaryVisualization,
        ThresholdSlider,
        RowSelector,
        SecondaryVisualization,
        SingleRowHeatmap,
        SSVisualization,
        SurvivalCurvesPlot,
        TopRowsPicker,
        ColumnOptionsComponent,
        TopOptionsComponent
    ],
    providers: [NumberFormatPipe] // required for DI in SingleRowHeatmap
})

export class SSModule { }