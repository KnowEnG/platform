import {Component, OnInit, OnDestroy} from '@angular/core';
import {HashLocationStrategy, LocationStrategy} from '@angular/common';

import {ServerStatusService} from '../../services/common/ServerStatusService';
import {PerfMonService} from '../../services/common/PerfMonService';

import {Subscription} from 'rxjs/Subscription';
import {Observable} from 'rxjs/Observable';

@Component({
    selector: 'app',
    template: `
        <router-outlet></router-outlet>
    `,
    providers: [{provide: LocationStrategy, useClass: HashLocationStrategy}]
})

export class App implements OnInit, OnDestroy {
    private DEBUG: boolean = false;
    private timerSub: Subscription;
    
    constructor(private statusService: ServerStatusService, 
                private perfMon: PerfMonService) { 
    }
    
    ngOnInit() {
        if (this.DEBUG) {
            let timer = Observable.timer(3000, 1000);
            this.timerSub = timer.subscribe(() => this.perfMon.heapSize());
        }
    }
    
    ngOnDestroy() {
        if (this.DEBUG) {
            this.timerSub.unsubscribe();
        }
    }
}
