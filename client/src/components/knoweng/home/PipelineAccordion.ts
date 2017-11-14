import {Component, OnInit} from '@angular/core';

import {Pipeline} from '../../../models/knoweng/Pipeline';
import {PipelineService} from '../../../services/knoweng/PipelineService';

@Component({
    moduleId: module.id,
    selector: 'pipeline-accordion',
    templateUrl: './PipelineAccordion.html',
    styleUrls: ['./PipelineAccordion.css']
})

export class PipelineAccordion implements OnInit {
    class = 'relative';
    
    pipelines: Pipeline[] = [];
    selectedIndex: number = null;
    constructor(public pipelineService: PipelineService) {
        this.pipelines = this.pipelineService.getPipelines();
    }
    ngOnInit() {
    }
    onClickPanel(index: number) {
        if (index == this.selectedIndex) {
            this.selectedIndex = null;
        } else {
            this.selectedIndex = index;
        }
    }
}
