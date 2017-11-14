import {NgModule} from '@angular/core';
import {RouterModule} from '@angular/router';

import {Data} from './Data';

@NgModule({
    imports: [RouterModule.forChild([
        { path: '', component: Data }
    ])],
    exports: [RouterModule]
})

export class DataRoutingModule {}
