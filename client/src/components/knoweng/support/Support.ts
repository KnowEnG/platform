import {Component, Injectable, OnInit, OnDestroy} from '@angular/core';
import {ActivatedRoute, Params, Router, NavigationEnd} from '@angular/router';
import {DomSanitizer, SafeResourceUrl} from '@angular/platform-browser';
import {Http, Headers, Response} from '@angular/http';

import {Observable} from 'rxjs/Observable';
import {Subscription} from 'rxjs/Subscription';

import {GoogleAnalyticsService} from '../../../services/common/GoogleAnalyticsService';

@Component({
    moduleId: module.id,
    selector: 'support',
    templateUrl: './Support.html',
    styleUrls: ['./Support.css', '../common/SupportAndWelcomeText.css']
})

export class Support implements OnInit, OnDestroy {
    class = 'relative';
    
    
    // URL to "client/data/youtube.json", which contains a list of 
    // video codes to present on the support page
    // For example: "4n_x6ZlXg38" => from https://www.youtube.com/watch?v=4n_x6ZlXg38
    // TODO: Could we query the YouTube api for a particular playlist instead?
    private videosUrl = '/static/data/youtube.json';
    private videoCodes: string[] = [];
    private safeVideoUrls: SafeResourceUrl[] = [];
    
    topics = ['contact', 'training', 'about', 'manuscript'];
    menuSelection: string;
    
    routeSub: Subscription;
   
    constructor(private _route: ActivatedRoute,
                private _router: Router,
                private _sanitizer: DomSanitizer,
                private _http: Http,
                private _googleAnalytics: GoogleAnalyticsService) {
        this._router.events.subscribe(event => {
          if (event instanceof NavigationEnd) {
            this._googleAnalytics.emitPageView(event.urlAfterRedirects);
          }
        });
    }
    ngOnInit() {
        this.routeSub = this._route.params.subscribe((params : Params) => {
            // this will change menuSelection, which updates display styles
            let topic = params['topic'];
            if (topic && this.topics.indexOf(topic) !== -1) {
                this.menuSelection = topic;
            } else {
                this.selectTopic(this.topics[0]);
            }
        });
        
        let headers = new Headers();
        headers.append('Content-Type', 'application/json');
    
        this._http.get(this.videosUrl, {headers: headers})
          .map((res: Response) => res.json())
          .catch((error: any) => Observable.throw(error))
          .subscribe((videoCodes: any) => {
              this.videoCodes = videoCodes;
              this.safeVideoUrls = [];
              this.videoCodes.forEach(code => this.safeVideoUrls.push(this.sanitizeYoutubeUrl(code)));
          });
          
       
    }
    ngOnDestroy() {
        this.routeSub.unsubscribe();
    }
    sanitizeYoutubeUrl(code: string) {
        return this._sanitizer.bypassSecurityTrustResourceUrl('https://www.youtube.com/embed/' + code);
    }
    selectTopic(topic: string) {
        this._router.navigate(["/support/" + topic])
    }
}
