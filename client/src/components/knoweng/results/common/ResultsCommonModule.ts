import {NgModule} from '@angular/core';
import {CommonModule} from '@angular/common';
import {PopoverModule} from 'ngx-bootstrap';

import {NestCommonModule} from '../../../common/NestCommonModule';
import {KnowengCommonModule} from '../../common/KnowengCommonModule';

import {CellHeatmap} from './CellHeatmap';
import {ColumnLabelContextMenu} from './ColumnLabelContextMenu';
import {GradientLegend} from './GradientLegend';
import {PieChart} from './PieChart';
import {JobSummary} from './JobSummary';
import {ColorGradientPicker} from './ColorGradientPicker';
import {RowLabelContextMenu} from './RowLabelContextMenu';
import {Slider} from './Slider';
import {NumberFormatPipe} from '../../../../pipes/knoweng/NumberFormatPipe';
import {FileNamePipe} from '../../../../pipes/knoweng/FileNamePipe';

@NgModule({
    imports: [PopoverModule.forRoot(), CommonModule, NestCommonModule, KnowengCommonModule],
    declarations: [
        CellHeatmap, 
        ColumnLabelContextMenu,
        GradientLegend,
        PieChart,
        JobSummary,
        RowLabelContextMenu,
        Slider,
        NumberFormatPipe,
        FileNamePipe,
        ColorGradientPicker],
    exports: [
        CellHeatmap,
        ColumnLabelContextMenu,
        GradientLegend,
        PieChart,
        JobSummary,
        RowLabelContextMenu,
        Slider,
        NumberFormatPipe,
        FileNamePipe,
        ColorGradientPicker]
})

export class ResultsCommonModule { }