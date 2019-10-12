import {NgModule} from '@angular/core';
import {CommonModule} from '@angular/common';

import { AngularDraggableModule } from 'angular2-draggable';

import {NestCommonModule} from '../../../common/NestCommonModule';
import {ResultsCommonModule} from '../common/ResultsCommonModule';

import {CellRollover} from './CellRollover';
import {Clustergram} from './Clustergram';
import {ControlPanel} from './ControlPanel';
import {DataArea} from './DataArea';
import {SAVisualization} from './SAVisualization';
import {SignaturePlot} from './SignaturePlot';
import {SignatureSelector} from './SignatureSelector';

@NgModule({
    imports: [CommonModule, AngularDraggableModule, NestCommonModule, ResultsCommonModule],
    declarations: [
        CellRollover,
        Clustergram,
        ControlPanel,
        DataArea,
        SAVisualization,
        SignaturePlot,
        SignatureSelector
    ],
    exports: [SAVisualization]
})

export class SAModule { }