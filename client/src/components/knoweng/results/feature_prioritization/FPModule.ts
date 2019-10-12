import {NgModule} from '@angular/core';
import {CommonModule} from '@angular/common';

import { AngularDraggableModule } from 'angular2-draggable';

import {ResultsCommonModule} from '../common/ResultsCommonModule';

import {CellRollover} from './CellRollover';
import {Clustergram} from './Clustergram';
import {ControlPanel} from './ControlPanel';
import {DataArea} from './DataArea';
import {FPVisualization} from './FPVisualization';
import {ResponseSelector} from './ResponseSelector';
import {ResponsePlot} from './ResponsePlot';

@NgModule({
    imports: [CommonModule, AngularDraggableModule, ResultsCommonModule],
    declarations: [
        CellRollover,
        Clustergram,
        ControlPanel,
        DataArea,
        FPVisualization,
        ResponseSelector,
        ResponsePlot
    ],
    exports: [FPVisualization]
})

export class FPModule { }