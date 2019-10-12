import {Component, OnInit} from '@angular/core';
import {Router, NavigationEnd} from "@angular/router";

import {GoogleAnalyticsService} from '../../../services/common/GoogleAnalyticsService';

@Component({
    moduleId: module.id,
    selector: 'home',
    templateUrl: './Home.html',
    styleUrls: ['./Home.css']
})

export class Home implements OnInit {
    class = 'relative';
    constructor(private router: Router, private googleAnalytics: GoogleAnalyticsService) {
        this.router.events.subscribe(event => {
          if (event instanceof NavigationEnd) {
            this.googleAnalytics.emitPageView(event.urlAfterRedirects);
          }
        });
    }
    
    ngOnInit() {
    }
}
