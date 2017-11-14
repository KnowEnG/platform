import {Injectable} from '@angular/core';
import {Headers} from '@angular/http';
import {AuthHttp} from 'angular2-jwt';

import {Observable} from 'rxjs/Observable';

import 'rxjs/add/observable/throw';

@Injectable()
export class LogService {
  private _logsUrl: string = '/api/v2/logs';
  private _defaultLogLevel = 'info';
  
  constructor(private authHttp: AuthHttp) {
    // no need to fetch anything from this endpoint
  }
  
  /**
   * Convenience methods that wrap logger.log
   * 
   * logger.error and logger.critical accept an optional stacktrace (string or object))
   */
  critical(message: string, stack?: string): void { return this.log('critical', message, stack);  };
  error(message: string, stack?: string): void { return this.log('error', message, stack); };
  warn(message: string): void { return this.log('warn', message); };
  debug(message: string): void { return this.log('debug', message); };
  info(message: string): void { return this.log('info', message); };
  
  /**
   * POST a log message to the web server, to echo it to the server logs
   */
  log(level: string, message: string, stack?: string): void {
    var headers = new Headers();
    headers.append('Content-Type', 'application/json');
        
    // TODO: how should we handle logging "objects"?
    // FIXME: This works, but it is not very elegant and the output is not as readable as it could be... 
    if (typeof message !== 'string') {
      message = JSON.stringify(message);
    }
    
    // post the new log message to the server
    // TODO: Format and send "sent" datetime?
    var logItem = { level: level || this._defaultLogLevel, message: message, stack: stack };
    this.authHttp.post(this._logsUrl, JSON.stringify(logItem), {headers: headers})
                 .catch((error: any) => Observable.throw(error))
                 .subscribe(
                     // Echo to console
                     data => console.log("Log message forwarded to server: ", logItem),
                     err => { 
                       console.error("Log message FAILED forwarding to server: ", logItem);
                       console.error("Caused by:", err.toString());
                     });
  };
};
