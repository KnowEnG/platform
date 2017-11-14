import {Component, Injectable, OnInit, OnDestroy} from '@angular/core';
import {ActivatedRoute, Params, Router} from '@angular/router';
import { DomSanitizer } from '@angular/platform-browser';
import {Http, Headers, Response} from '@angular/http';

import {Observable} from 'rxjs/Observable';
import {Subscription} from 'rxjs/Subscription';

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
    
    topics = ['contact', 'training', 'about'];
    menuSelection: string;
    
    routeSub: Subscription;

    constructor(
        private _route: ActivatedRoute,
        private _router: Router,
        private _sanitizer: DomSanitizer,
        private _http: Http) {
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
            console.log(this.menuSelection);
        });
        
        let headers = new Headers();
        headers.append('Content-Type', 'application/json');
    
        this._http.get(this.videosUrl, {headers: headers})
          .map((res: Response) => res.json())
          .catch((error: any) => Observable.throw(error))
          .subscribe((videoCodes: any) => {
              this.videoCodes = videoCodes;
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