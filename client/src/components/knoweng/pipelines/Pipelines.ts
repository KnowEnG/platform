import {Component, OnChanges, SimpleChange} from '@angular/core';
import {Router, NavigationEnd} from "@angular/router";

import {GoogleAnalyticsService} from '../../../services/common/GoogleAnalyticsService';

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
    constructor(private router: Router, private googleAnalytics: GoogleAnalyticsService) {
        this.router.events.subscribe(event => {
          if (event instanceof NavigationEnd) {
            this.googleAnalytics.emitPageView(event.urlAfterRedirects);
          }
        });
    }
    ngOnChanges(changes: {[propertyName: string]: SimpleChange}) {
    }
    onTemplateSelected(template: string) {
    }
    onPipelineSelected(pipeline: Pipeline) {
        this.pipeline = pipeline;
    }
}
