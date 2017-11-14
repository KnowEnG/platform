import {NgModule} from '@angular/core';
import {RouterModule} from '@angular/router';

import {Network} from './Network';

@NgModule({
    imports: [RouterModule.forChild([
        { path: '', component: Network }
    ])],
    exports: [RouterModule]
})

export class NetworkRoutingModule {}
