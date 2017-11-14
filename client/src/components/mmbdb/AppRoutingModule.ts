import {NgModule} from '@angular/core';
import {RouterModule, Routes} from '@angular/router';
import {AuthHttp, AuthConfig} from 'angular2-jwt';
import {Http} from '@angular/http';

import {Logout} from './../common/Logout';
import {LoginFormComponent} from './LoginFormComponent';
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
        loadChildren: 'dist/components/mmbdb/MmbdbModule#MmbdbModule'
    }  
]

@NgModule({
    imports: [RouterModule.forRoot(publicroutes, {useHash: true })],
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