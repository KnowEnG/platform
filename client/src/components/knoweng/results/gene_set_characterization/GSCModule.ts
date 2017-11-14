import {NgModule} from '@angular/core';
import {CommonModule} from '@angular/common';

import {NestCommonModule} from '../../../common/NestCommonModule';
import {ResultsCommonModule} from '../common/ResultsCommonModule';

import {Clustergram} from './Clustergram';
import {ColumnLabelContextMenu} from './ColumnLabelContextMenu';
import {ComparisonGeneSetSelector} from './ComparisonGeneSetSelector';
import {ControlPanel} from './ControlPanel';
import {DataArea} from './DataArea';
import {GeneSetLevelRollover} from './GeneSetLevelRollover';
import {GradientFilter} from './GradientFilter';
import {GradientNumberLine} from './GradientNumberLine';
import {GSCVisualization} from './GSCVisualization';
import {RowLabelContextMenu} from './RowLabelContextMenu';
import {UserGeneSetSelector} from './UserGeneSetSelector';

@NgModule({
    imports: [CommonModule, NestCommonModule, ResultsCommonModule],
    declarations: [
        Clustergram,
        ColumnLabelContextMenu,
        ComparisonGeneSetSelector,
        ControlPanel,
        DataArea,
        GeneSetLevelRollover,
        GradientFilter,
        GradientNumberLine,
        GSCVisualization,
        RowLabelContextMenu,
        UserGeneSetSelector
    ],
    exports: [GSCVisualization]
})

export class GSCModule { }