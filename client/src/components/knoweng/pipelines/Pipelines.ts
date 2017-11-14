import {Component, OnChanges, SimpleChange} from '@angular/core';

import {Pipeline} from '../../../models/knoweng/Pipeline';

@Component({
    moduleId: module.id,
    selector: 'pipelines',
    templateUrl: './Pipelines.html',
    styleUrls: ['./Pipelines.css']
})

export class Pipelines implements OnChanges {
    class = 'relative';
    
    pipeline: Pipeline = null;
    constructor() {
    }
    ngOnChanges(changes: {[propertyName: string]: SimpleChange}) {
    }
    onTemplateSelected(template: string) {
    }
    onPipelineSelected(pipeline: Pipeline) {
        this.pipeline = pipeline;
    }
}
