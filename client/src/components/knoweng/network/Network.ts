import {Component, OnInit} from '@angular/core';
import {Router, NavigationEnd} from "@angular/router";

import {GoogleAnalyticsService} from '../../../services/common/GoogleAnalyticsService';
import {tokenNotExpired} from 'angular2-jwt';

@Component({
    moduleId: module.id,
    selector: 'results',
    templateUrl: './Network.html',
    styleUrls: ['./Network.css']
})
//@CanActivate(() => tokenNotExpired())

export class Network implements OnInit {
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
