import {Component, OnChanges, SimpleChange, EventEmitter, Output} from '@angular/core';

import {Pipeline} from '../../../models/knoweng/Pipeline';

@Component({
    moduleId: module.id,
    selector: 'pipeline-selector',
    templateUrl: './PipelineSelector.html',
    styleUrls: ['./PipelineSelector.css']
})

export class PipelineSelector implements OnChanges {
    class = 'relative';
    
    @Output()
    templateSelected: EventEmitter<string> = new EventEmitter<string>();
    
    @Output()
    pipelineSelected: EventEmitter<Pipeline> = new EventEmitter<Pipeline>();
    
    constructor() {
    }
    ngOnChanges(changes: {[propertyName: string]: SimpleChange}) {
    }
}
