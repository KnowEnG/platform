import {NgModule} from '@angular/core';
import {RouterModule, Routes} from '@angular/router';
import {AuthHttp, AuthConfig} from 'angular2-jwt';
import {Http} from '@angular/http';

import {SessionService} from '../../services/common/SessionService';
import {AuthGuard} from '../../services/common/AuthGuard';

import {AuthorizedUserApp} from './AuthorizedUserApp';

const routes: Routes = [
    {
        path: '',
        component: AuthorizedUserApp,
        canActivate: [AuthGuard],
        children: [
            {
                path: '',
                canActivate: [AuthGuard],
                children: [
                    {
                        path: 'home',
                        loadChildren: 'dist/components/knoweng/home/HomeModule#HomeModule',
                    },
                    {
                        path: 'pipelines',
                        loadChildren: 'dist/components/knoweng/pipelines/PipelinesModule#PipelinesModule'
                    },
                    {
                        path: 'data',
                        loadChildren: 'dist/components/knoweng/results/ResultsModule#ResultsModule'
                    },
                    {
                        path: 'network',
                        loadChildren: 'dist/components/knoweng/network/NetworkModule#NetworkModule'
                    },
                    {
                        path: 'support',
                        loadChildren: 'dist/components/knoweng/support/SupportModule#SupportModule',
                    },
                    {
                        path: '',
                        redirectTo: 'home'
                    }
                ]
            }
        ]
    }
];

@NgModule({
    imports: [RouterModule.forChild(routes)],
    exports: [RouterModule]
})

export class AuthorizedUserAppRoutingModule {}
