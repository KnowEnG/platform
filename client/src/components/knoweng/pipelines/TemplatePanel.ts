import {Component, OnChanges, SimpleChange, EventEmitter, Output} from '@angular/core';

@Component({
    moduleId: module.id,
    selector: 'template-panel',
    templateUrl: './TemplatePanel.html',
    styleUrls: ['./TemplatePanel.css']
})

export class TemplatePanel implements OnChanges {
    class = 'relative';
    
    @Output()
    templateSelected: EventEmitter<string> = new EventEmitter<string>();
    
    filters: string[] = ["All", "Favorites", "Recent"];
    selectedFilter = "All";
    templates: string[] = [
        /* hiding even the dummy data for now, just so users don't get the wrong idea
        "Clustering_hierarchical_092215_P1",
        "Clustering_hierarchical_092215_P1",
        "Clustering_hierarchical_092215_P1",
        "Clustering_hierarchical_092215_P1",
        "Clustering_hierarchical_092215_P1",
        "Clustering_hierarchical_092215_P1",
        "Clustering_hierarchical_092215_P1",
        "Clustering_hierarchical_092215_P1",
        "Clustering_hierarchical_092215_P1",
        "Clustering_hierarchical_092215_P1",
        "Clustering_hierarchical_092215_P1",
        "Clustering_hierarchical_092215_P1",
        "Clustering_hierarchical_092215_P1"
        */
    ];
    constructor() {
    }
    ngOnChanges(changes: {[propertyName: string]: SimpleChange}) {
    }
    onClickFilter(filter: string) {
        this.selectedFilter = filter;
    }
    onClickTemplate(template: string) {
        this.templateSelected.emit(template);
    }
}
