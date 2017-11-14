import {NgModule} from '@angular/core';
import {RouterModule, Routes} from '@angular/router';

import {AuthGuard} from '../../services/common/AuthGuard';
import {MmbdbComponent} from './MmbdbComponent';
import {CohortPlaceholder} from './CohortPlaceholder';
import {IndividualPlaceholder} from './IndividualPlaceholder';
import {CohortComparisonTool} from './CohortComparisonTool';
import {CreateReportsComponent} from './CreateReportsComponent';
import {DiscoverCohortsComponent} from './DiscoverCohortsComponent';
import {BuildComparisonComponent} from './BuildComparisonComponent';
import {GettingStartedComponent} from './GettingStartedComponent';

const routes: Routes = [
    {
        path: '',
        component: MmbdbComponent,
        canActivate: [AuthGuard],
        children: [
            {
                path: '',
                canActivate: [AuthGuard],
                children: [
                    {
                        path: '',
                        redirectTo: 'getting-started',
                        pathMatch: 'full'
                    },
                    {
                        path: 'discover-cohorts',
                        component: DiscoverCohortsComponent
                    },
                    {
                        path: 'build-comparison',
                        component: BuildComparisonComponent
                    },
                    {
                        path: 'getting-started',
                        component: GettingStartedComponent
                    },
                    {
                        path: 'cohorts',
                        component: CohortPlaceholder
                    },
                    {
                        path: 'individuals',
                        component: IndividualPlaceholder
                    },
                    {
                        path: 'compare/:id',
                        component: CohortComparisonTool
                    },
                    {
                        path: 'create-reports',
                        component: CreateReportsComponent
                    }  
                  ]
            }
        ]
    }
]
    
@NgModule({
    imports: [RouterModule.forChild(routes)],
    exports: [RouterModule]
})

export class MmbdbRoutingModule {}