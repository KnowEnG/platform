import {Component} from '@angular/core';
import {Router} from '@angular/router';
import {Observable} from 'rxjs/Observable';
import {SessionService} from '../../services/common/SessionService';
import {LogService} from '../../services/common/LogService';

@Component({
    moduleId: module.id,
    templateUrl: './Login.html'
})

export class Login {
    class = 'relative';
    
    loginFormData = new ControlGroup("", "");
    errorMessage: string = "Please log in.";
    constructor(
            private sessionService: SessionService,
            private router: Router,
            private logger: LogService) {
    }
            
    submitIfEnter(event: Event): boolean {
        if ((<any>event).keyCode == '13') {
            this.submit();
        }
        return false; // don't bubble up
    }
    submit() {
        var messageStream: Observable<string> = this.sessionService.createSession(
            this.loginFormData.username,
            this.loginFormData.password,
            ''
        );

        messageStream.subscribe(
            data => {
                this.errorMessage = data;
            },
            err => {
                this.errorMessage = err;
                this.logger.error(err);
            },
            () => {
                let redirect = this.sessionService.redirectUrl ? this.sessionService.redirectUrl : '/';
                this.router.navigate([redirect]);
            }
        );
    }
}

export class ControlGroup {
    constructor(
        public username: string,
        public password: string
    ) {}
}
