import {Component, OnChanges, SimpleChange, EventEmitter, Output} from '@angular/core';

import {HelpContent} from '../../../models/knoweng/HelpContent';
import {Pipeline} from '../../../models/knoweng/Pipeline';
import {PipelineService} from '../../../services/knoweng/PipelineService';
import {LogService} from '../../../services/common/LogService';

@Component({
    moduleId: module.id,
    selector: 'pipeline-list',
    templateUrl: './PipelineList.html',
    styleUrls: ['./PipelineList.css']
})

export class PipelineList implements OnChanges {
    class = 'relative';

    @Output()
    pipelineSelected: EventEmitter<Pipeline> = new EventEmitter<Pipeline>();

    pipelines: Pipeline[] = [];

    selectedIndex: number = null;

    /* currently displayed help content. */
    helpContent: HelpContent = null;

    constructor(private logger: LogService, private pipelineService: PipelineService) {
        this.pipelines = this.pipelineService.getPipelines();
    }
    ngOnChanges(changes: {[propertyName: string]: SimpleChange}) {
        this.selectedIndex = 0;
        this.helpContent = this.pipelines[this.selectedIndex].overview;
    }
    onPipelineMouseEnter(index: number) {
        this.selectedIndex = index;
        this.helpContent = this.pipelines[index].overview;
    }
    /*onPipelineStart(pipeline: Pipeline) {
        this.pipelineSelected.emit(pipeline);
    }*/
}
