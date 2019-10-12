import {Injectable} from '@angular/core';
import {CanActivate, Router, ActivatedRouteSnapshot, RouterStateSnapshot, CanActivateChild, CanLoad, Route} from '@angular/router';
import {Observable} from 'rxjs/Observable';
import {SessionService} from './SessionService';

import {LogService} from './LogService';

@Injectable()
export class AuthGuard implements CanActivate, CanActivateChild, CanLoad {

    constructor(private sessService: SessionService, private router: Router, private logger: LogService) {
    }
    
    canActivate(route: ActivatedRouteSnapshot, state: RouterStateSnapshot): boolean {
        let url: string = state.url;
        return this.checkLogin(url);
    }
    
    canActivateChild(route:ActivatedRouteSnapshot, state: RouterStateSnapshot): boolean {
        return this.canActivate(route, state);
    }
    
    canLoad(route: Route): boolean {
        let url = `/${route.path}`;
        return this.checkLogin(url);
    }
  
    checkLogin(url: string): boolean {
        if (this.sessService.hasValidSession()) {
            return true;
        } else {
            let authCode: string = this.getAuthorizationCodeFromUrl(
                window.location.search, window.location.hash);
            if (authCode !== null) {
                let messageStream: Observable<string> = this.sessService.createSession(
                    '',
                    '',
                    authCode);

                messageStream.subscribe(
                    data => {
                        // this is just a message with a status update
                        // successful authentication is announced via stream
                        // completion
                    },
                    err => {
                        this.logger.info("Failed to check token validity: " + err);
                        this.sessService.redirectToLogin();
                    },
                    () => {
                        // report authentication status to the logger
                        this.logger.debug("Successful login");
                        this.router.navigate( ["/home"] );
                    }
                );
            } else {
                this.sessService.redirectToLogin();
                return false;
            }
        }
    }

    getAuthorizationCodeFromUrl(searchPortion: string, hashPortion: string): string {
        // have to do this manually; RouteParams not available outside of routes

        // depending on how this page was redirected, the query may end up in the
        // search or the hash
        var codeString: string = searchPortion + '&' + hashPortion;

        // looking for 'code=KEEPTHISPART', optionally followed by
        // '&OTHER-STUFF-WE-CAN-IGNORE'
        var prefix: string = 'code=';
        var codeStart: number = codeString.indexOf(prefix);
        if (codeStart > -1) {
            var codeEnd: number = codeString.indexOf('&', codeStart);
            if (codeEnd > -1) {
                codeString = codeString.substring(codeStart+prefix.length, codeEnd);
            } else {
                codeString = codeString.substring(codeStart+prefix.length);
            }
        } else {
            codeString = null;
        }
        return codeString;
    }
}