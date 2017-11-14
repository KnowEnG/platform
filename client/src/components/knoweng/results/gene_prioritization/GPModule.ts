import {NgModule} from '@angular/core';
import {CommonModule} from '@angular/common';

import {ResultsCommonModule} from '../common/ResultsCommonModule';

import {CellRollover} from './CellRollover';
import {Clustergram} from './Clustergram';
import {ColumnLabelContextMenu} from './ColumnLabelContextMenu';
import {ControlPanel} from './ControlPanel';
import {DataArea} from './DataArea';
import {GPVisualization} from './GPVisualization';
import {GradientLegend} from './GradientLegend';
import {ResponseSelector} from './ResponseSelector';
import {ResponsePlot} from './ResponsePlot';
import {RowLabelContextMenu} from './RowLabelContextMenu';
import {Slider} from './Slider';

@NgModule({
    imports: [CommonModule, ResultsCommonModule],
    declarations: [
        CellRollover,
        Clustergram,
        ColumnLabelContextMenu,
        ControlPanel,
        DataArea,
        GPVisualization,
        GradientLegend,
        ResponseSelector,
        ResponsePlot,
        RowLabelContextMenu,
        Slider
    ],
    exports: [GPVisualization]
})

export class GPModule { }