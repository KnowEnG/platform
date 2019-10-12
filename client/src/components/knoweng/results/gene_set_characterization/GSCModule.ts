import {NgModule} from '@angular/core';
import {CommonModule} from '@angular/common';

import { AngularDraggableModule } from 'angular2-draggable';

import {NestCommonModule} from '../../../common/NestCommonModule';
import {ResultsCommonModule} from '../common/ResultsCommonModule';

import {Clustergram} from './Clustergram';
import {GSCColumnLabelContextMenu} from './GSCColumnLabelContextMenu';
import {ComparisonGeneSetSelector} from './ComparisonGeneSetSelector';
import {ControlPanel} from './ControlPanel';
import {DataArea} from './DataArea';
import {GeneSetLevelRollover} from './GeneSetLevelRollover';
import {GradientFilter} from './GradientFilter';
import {GradientNumberLine} from './GradientNumberLine';
import {GSCVisualization} from './GSCVisualization';
import {GSCRowLabelContextMenu} from './GSCRowLabelContextMenu';
import {UserGeneSetSelector} from './UserGeneSetSelector';

@NgModule({
    imports: [CommonModule, AngularDraggableModule, NestCommonModule, ResultsCommonModule],
    declarations: [
        Clustergram,
        GSCColumnLabelContextMenu,
        ComparisonGeneSetSelector,
        ControlPanel,
        DataArea,
        GeneSetLevelRollover,
        GradientFilter,
        GradientNumberLine,
        GSCVisualization,
        GSCRowLabelContextMenu,
        UserGeneSetSelector
    ],
    exports: [GSCVisualization]
})

export class GSCModule { }