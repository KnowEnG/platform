import {NgModule} from '@angular/core';
import {CommonModule} from '@angular/common';

import {KnowengCommonModule} from '../common/KnowengCommonModule';
import {HomeRoutingModule} from './HomeRoutingModule';

import {Home} from './Home';
import {PipelineAccordion} from './PipelineAccordion';
import {PipelinePanel} from './PipelinePanel';
import {MainContentPanel} from './MainContentPanel';
import {MainContentTable} from './MainContentTable';
import {RecentResultsTable} from './RecentResultsTable';
import {ResultsContextMenu} from './ResultsContextMenu';
import {WelcomeText} from './WelcomeText';

@NgModule({
    imports: [CommonModule, HomeRoutingModule, KnowengCommonModule],
    declarations: [Home, PipelineAccordion, PipelinePanel, MainContentPanel, MainContentTable, RecentResultsTable, ResultsContextMenu, WelcomeText],
    exports: []
})

export class HomeModule { }