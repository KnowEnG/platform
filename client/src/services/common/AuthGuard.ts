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
            let sessionId: string = this.getSessionIdFromUrl(
                window.location.search, window.location.hash);
            if (sessionId !== null) {
                let messageStream: Observable<string> = this.sessService.createSession(
                    '',
                    '',
                    sessionId);

                messageStream.subscribe(
                    data => {
                        // report authentication status to the logger
                        this.logger.debug("Successful login: " + data);
                        this.router.navigate( ["/home"] );
                    },
                    err => {
                        this.logger.info("Failed to check token validity: " + err);
                        this.sessService.redirectToLogin();
                    }
                );
            } else {
                this.sessService.redirectToLogin();
                return false;
            }
        }
        this.sessService.redirectUrl = url;
        this.router.navigate( ["/"] );
    }

    getSessionIdFromUrl(searchPortion: string, hashPortion: string): string {
        // have to do this manually; RouteParams not available outside of routes

        // depending on how this page was redirected, the query may end up in the
        // search or the hash
        var tokenString: string = searchPortion + '&' + hashPortion;

        // looking for 'mysession=KEEPTHISPART', optionally followed by
        // '&OTHER-STUFF-WE-CAN-IGNORE'
        var prefix: string = 'mysession=';
        var sessionStart: number = tokenString.indexOf(prefix);
        if (sessionStart > -1) {
            var sessionEnd: number = tokenString.indexOf('&', sessionStart);
            if (sessionEnd > -1) {
                tokenString = tokenString.substring(sessionStart+prefix.length, sessionEnd);
            } else {
                tokenString = tokenString.substring(sessionStart+prefix.length);
            }
        } else {
            tokenString = null;
        }
        return tokenString;
    }
}