import {Injectable} from '@angular/core';
import {Headers, Http, Response} from '@angular/http';
import {Observable} from 'rxjs/Observable';

import 'rxjs/add/observable/timer';
import 'rxjs/add/operator/map';
import 'rxjs/add/operator/catch';

import {LogService} from '../../services/common/LogService';

export class ServerStatus {
    maxUploadSize: number = null;
    constructor(
        public sha: string,
        public runlevel: string,
        public hzHost: string,
        maxUploadSize: string) {
            this.maxUploadSize = parseInt(maxUploadSize, 10) || null;
    }
}

@Injectable()
export class ServerStatusService {
  public status: ServerStatus;                   // Model to store cached status
  private statusUrl = '/static/dist/status.json';     // URL to poll for status
  private initialDelayMs = 1800000;              // How long before we start polling
  private pollIntervalMs = 3600000;              // How often to poll, once we start
  
  // no need to auth - anybody can navigate to /static/status.json in their browser
  constructor(private http: Http, private logger: LogService) {
    // Set up polling on our status endpoint
    let timer = Observable.timer(this.initialDelayMs, this.pollIntervalMs);
    this.getStatus();
    timer.subscribe(() => { this.getStatus(); });
  }
  
  /**
   * GET the current version number from the server's status.json
   */
  getStatus(): Observable<ServerStatus> {
    let headers = new Headers();
    headers.append('Content-Type', 'application/json');
    
    // Build an Observable ServerStatus
    let retVal = this.http.get(this.statusUrl, {headers: headers})
      .map((res: Response) => res.json())
      .catch((error: any) => Observable.throw(error)).share();
    
    // Subscribe to the Observable to retrieve the status  
    retVal.subscribe((data: ServerStatus) => {
      var status = data;
      
      // If this is the first time we've grabbed the status, store it
      this.status || (this.status = status);
      
      // If we see a new SHA hash, store it and prompt the user to refresh their client
      (this.status.sha === status.sha) || ((this.status = status) &&
        alert('A new version of the web client is available! '
          + 'Refresh your browser to use the new version.'));
    },
    (err: any) => this.logger.error("Failed to fetch server version.", err));
      
    // Return an Observable to provide the status to others
    return retVal;
  };
};
