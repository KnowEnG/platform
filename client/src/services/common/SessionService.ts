import {Location} from '@angular/common';
import {Router} from '@angular/router';
import {Injectable} from '@angular/core';
import {Http, Headers} from '@angular/http';
import {Observable} from 'rxjs/Observable';
import {BehaviorSubject} from 'rxjs/BehaviorSubject';
import {JwtHelper} from 'angular2-jwt';

import {ServerStatusService} from './ServerStatusService';

@Injectable()
export class SessionService {
    // store the URL so we can redirect after logging in
    redirectUrl: string;

    // The login route for the KnowEnG dashboard
    private _staticLoginRoute = 'login';

    private _sessionUrl = '/api/v2/sessions';

    // if changing this, check angular2-jwt docs for consequences
    private _tokenKey = 'id_token';

    private _tokenSubject: BehaviorSubject<any> = new BehaviorSubject<any>({});

    private _cilogonLoginUrl = '';

    constructor(private http: Http, private location: Location, private router: Router, private statusService: ServerStatusService) {
    }

    getLoginUrl(presentStaticLogin: boolean = false) {
        // Short-circuit for our static login route
        if (presentStaticLogin) {
            return this._staticLoginRoute;
        }

        // Check the latest server status to determine the cilogon url
        if (this.statusService.status) {
            this._cilogonLoginUrl = this.statusService.status.cilogonLoginUrl;
        }

        // If cilogonLoginUrl is not set, return our static login route
        if (!this._cilogonLoginUrl) {
            return this._staticLoginRoute;
        }

        // If cilogon auth is enabled and we weren't told explicitly to send
        // the user to the nest login page, redirect to cilogon
        // TODO: how to detect protocol?
        return this._cilogonLoginUrl;
    }

    redirectToLogin(presentStaticLogin: boolean = false) {
        let loginUrl = this.getLoginUrl(presentStaticLogin);

        if (loginUrl === this._staticLoginRoute) {
            // Handle relative urls with router
            this.router.navigateByUrl(this._staticLoginRoute);
        } else {
            // Handle absolute urls with location.href
            window.location.href = loginUrl;
        }
    }

    tokenChanged() {
        return this._tokenSubject.asObservable();
    }

    //xx: pretend to be login function
    /**
     * Attempts to create a session by authenticating with the server. If
     * authentication succeeds, the server will return a token, which we'll
     * store to localStorage.
     * As of this writing, username and password are used for
     * NativeAuthenticationStrategy only, and authCode is used for
     * CILogonAuthenticationStrategy only. TODO clean this up as backend
     * evolves.
     */
    createSession(username: string, password: string, authCode: string): Observable<string> {
        // TODO BehaviorSubject is overkill
        var returnVal: BehaviorSubject<string> = new BehaviorSubject<string>("Authenticating...");

        var headers = new Headers();
        headers.append('Content-Type', 'application/json');
        // post the session info to the server
        var requestStream = this.http
            .post(
                this._sessionUrl,
                JSON.stringify({username: username, password: password, authCode: authCode}),
                {headers: headers})
            .map(res => res.json().access_token)
            .catch((error: any) => Observable.throw(error))
            .subscribe(
                data => {
                    localStorage.setItem(this._tokenKey, data);
                    this._tokenSubject.next(data);
                    returnVal.next("success!");
                    returnVal.complete();
                }, err => {
                    if (err.status == 403) {
                        // authentication failed
                        returnVal.error("Bad username or password.");
                    } else {
                        returnVal.error("Error communicating with server. Try again later or contact technical support.");
                    }
                }
            );
        return returnVal;
    }

    destroySession(): void {
        localStorage.removeItem(this._tokenKey);
    }

    /**
     * Returns the token if available.
     */
    getToken(): string {
        return localStorage.getItem(this._tokenKey);
    }

    /**
     * Returns true if there is currenly a valid session.
     */
    hasValidSession(): boolean {
        let token = this.getToken();
        let jwtHelper = new JwtHelper();
        let returnVal = token !== null && token.length != 0 && !jwtHelper.isTokenExpired(token);
        return returnVal;
    }


    /**
     * Returns the token payload if available.
     */
    getTokenPayload(): any {
        var jwtHelper: JwtHelper = new JwtHelper();
        var token: string = this.getToken();
        var returnVal: any = null;
        if (token !== null) {
            returnVal = jwtHelper.decodeToken(token);
        }
        return returnVal;
    }

    /**
     * Returns a field from the token payload if available.
     */
    getTokenPayloadField(fieldName: string): string {
        var payload: any = this.getTokenPayload();
        var returnVal: string = null;
        if (payload !== null && payload.hasOwnProperty(fieldName)) {
           returnVal = payload[fieldName];
        }
        return returnVal;
    }

    /**
     * Returns the user's given name if available.
     */
    getGivenName(): string {
        return this.getTokenPayloadField('given_name');
    }

    /**
     * Returns the user's family name if available.
     */
    getFamilyName(): string {
        return this.getTokenPayloadField('family_name');
    }

    /**
     * Returns the user's given and family name if available.
     */
    getDisplayName(): string {
        var givenName: string = this.getGivenName();
        var familyName: string = this.getFamilyName();
        var displayName: string =
            (givenName === null ? "" : givenName + " ") +
            (familyName === null ? "" : familyName);

        return displayName;
    }

    /**
     * Returns the user's profile image thumbnail URL if available.
     */
    getThumbnailUrl(): string {
        var returnVal: string = this.getTokenPayloadField('thumb_url');
        if (null !== returnVal && returnVal.length == 0) {
            returnVal = null;
        }
        return returnVal;
    }
}
