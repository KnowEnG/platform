import {Component, OnInit} from '@angular/core';
import {Router} from '@angular/router';
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
    
    constructor(
            private _router: Router) {
    }
    ngOnInit() {
    }
}
