// after Tabs.ts from ng-book2-r26.pdf
import {
    Component,
    Query,
    QueryList,
    ContentChildren,
    AfterContentInit,
    Input
} from '@angular/core';

// note we just use css to hide inactive tabs; might want to provide option
// of ngIf-based implementation, too. ngIf-based implementation would have lower
// upfront construction cost (only visible components would be instantiated)
// and lower resource use (change detection, etc.) but would incur construction
// cost with every tab switch
@Component({
    moduleId: module.id,
    selector: 'tab',
    //inputs: ['label'],
    styleUrls: ['./Tabset.css'],
    template: `
        <div role="tabpanel" class="tab-pane" [class.active]="active">
            <ng-content></ng-content>
        </div>
    `
})
export class Tab {
    class = 'relative';
    @Input('label') label: string;
    active: boolean = false;
    name: string;
}

@Component({
    moduleId: module.id,
    selector: 'tabset',
    styleUrls: ['./Tabset.css'],
    template: `
        <ul role="tablist" class="nav nav-tabs">
            <li *ngFor="let tab of tabs" role="presentation" [class.active]="tab.active">
                <a (click)="setActive(tab)" role="tab">{{ tab.label }}</a>
            </li>
        </ul>
        <div class="tab-content">
            <ng-content></ng-content>
        </div>
    `,
    providers: [QueryList]
})

export class Tabset implements AfterContentInit {
    class = 'relative';
    @ContentChildren(Tab) tabs: QueryList<Tab>;

    constructor(tabs:QueryList<Tab>) {
        this.tabs = tabs;
    }

    ngAfterContentInit() {
        this.tabs.toArray()[0].active = true;
    }

    setActive(tab: Tab) {
        this.tabs.toArray().forEach((t) => t.active = false);
        tab.active = true;
    }
}

