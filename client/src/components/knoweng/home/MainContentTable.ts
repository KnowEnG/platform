import {Component, OnInit} from '@angular/core';

@Component({
    moduleId: module.id,
    selector: 'main-content-table',
    templateUrl: './MainContentTable.html',
    styleUrls: ['./MainContentTable.css']
})

export class MainContentTable implements OnInit {
    class = 'relative';
    
    filters: string[] = ["Welcome", "Recent Results"];
    selectedFilter = "Welcome";
    constructor() {
    }
    ngOnInit() {
    }
    onClickFilter(filter: string) {
        this.selectedFilter = filter;
    }
}
