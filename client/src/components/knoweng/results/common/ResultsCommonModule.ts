import {NgModule} from '@angular/core';
import {CommonModule} from '@angular/common';

import {NestCommonModule} from '../../../common/NestCommonModule';
import {KnowengCommonModule} from '../../common/KnowengCommonModule';

import {CellHeatmap} from './CellHeatmap';
import {PieChart} from './PieChart';
import {JobSummary} from './JobSummary';

import {NumberFormatPipe} from '../../../../pipes/knoweng/NumberFormatPipe';

@NgModule({
    imports: [CommonModule, NestCommonModule, KnowengCommonModule],
    declarations: [
        CellHeatmap, 
        PieChart,
        JobSummary,
        NumberFormatPipe],
    exports: [CellHeatmap, PieChart, JobSummary, NumberFormatPipe]
})

export class ResultsCommonModule { }