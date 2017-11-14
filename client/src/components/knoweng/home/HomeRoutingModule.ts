import {NgModule} from '@angular/core';
import {RouterModule} from '@angular/router';

import {Home} from './Home';

@NgModule({
    imports: [RouterModule.forChild([
        { path: '', component: Home, pathMatch: 'full' }
    ])],
    exports: [RouterModule]
})

export class HomeRoutingModule {}
