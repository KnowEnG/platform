import {Component} from '@angular/core';
import {Router} from '@angular/router';

import {Login} from '../common/Login';
import {SessionService} from '../../services/common/SessionService';
import {LogService} from '../../services/common/LogService';

@Component({
    moduleId: module.id,
    templateUrl: './LoginFormComponent.html',
    styleUrls: ['./LoginFormComponent.css']
})


export class LoginFormComponent extends Login {
    class = 'relative';
    
    // note: this constructor may not be required in ng2 > v2.3.0
    // can't test until angular2-jwt catches up with rxjs
    constructor(
            sessionService: SessionService,
            router: Router,
            logger: LogService) {
        super(sessionService, router, logger);
    }
}
