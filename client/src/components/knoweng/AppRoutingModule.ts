import {NgModule} from '@angular/core';
import {RouterModule, Routes, PreloadAllModules} from '@angular/router';
import {AuthHttp, AuthConfig} from 'angular2-jwt';
import {Http} from '@angular/http';

import {LoginFormComponent} from './LoginFormComponent';
import {Logout} from './../common/Logout';

import {SessionService} from '../../services/common/SessionService';
import {AuthGuard} from '../../services/common/AuthGuard';

const publicroutes: Routes = [
    {
        path: 'login',
        component: LoginFormComponent
    },
    {
        path: 'logout',
        component: Logout
    },
    {
        path: '',
        loadChildren: 'dist/components/knoweng/AuthorizedUserAppModule#AuthorizedUserAppModule'
    }
]

@NgModule({
    imports: [RouterModule.forRoot(publicroutes, {
        useHash: true,
        preloadingStrategy: PreloadAllModules
    })],
    exports: [RouterModule],
    providers: [
        AuthGuard,
        SessionService,
        {provide: AuthHttp,
                  useFactory: (http: any) => {
                    return new AuthHttp(new AuthConfig({noJwtError: true}), http);
                  },
                  deps: [Http]
        }
    ]
})

export class AppRoutingModule {}
