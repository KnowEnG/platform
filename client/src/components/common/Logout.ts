import {Component, OnInit} from '@angular/core';
import {Router} from '@angular/router';
import {SessionService} from '../../services/common/SessionService';

@Component({
    selector: 'logout',
    template: `<h2> Goodbye! </h2>`,
    providers: [SessionService]
})

export class Logout implements OnInit {
    
    constructor(private _sessionService: SessionService, private _router: Router) {
    }
    
    ngOnInit() {
        this._sessionService.destroySession();
        this._sessionService.redirectToLogin();
    }
}
