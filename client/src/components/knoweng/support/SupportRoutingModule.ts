import {NgModule} from '@angular/core';
import {RouterModule} from '@angular/router';

import {Support} from './Support';

@NgModule({
    imports: [RouterModule.forChild([
            { path: ':topic', component: Support },
            { path: '', component: Support }
    ])],
    exports: [RouterModule]
})

export class SupportRoutingModule {}
