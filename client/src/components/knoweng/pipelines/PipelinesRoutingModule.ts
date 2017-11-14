import {NgModule} from '@angular/core';
import {RouterModule} from '@angular/router';

import {Pipelines} from './Pipelines';
import {FormContainer} from './FormContainer';

@NgModule({
    imports: [RouterModule.forChild([
        {
            path: '',
            children: [
                { path: ':id', component: FormContainer},
                { path: '', component: Pipelines }
            ]
        }
    ])],
    exports: [RouterModule]
})

export class PipelinesRoutingModule {}
