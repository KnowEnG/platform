import {AuthHttp} from 'angular2-jwt';
import {Headers, RequestOptions, ResponseContentType} from '@angular/http';
import {saveAs} from 'file-saver';
import {Observable} from 'rxjs/Observable';
import {Observer} from 'rxjs/Observer';

/**
 * This class provides methods for downloading files.
 */
export class DownloadUtilities {

    /**
     * Given a URL for a download from the nest server, saves the file.
     *
     * Args:
     *     url (string): URL for a download.
     *     authHttp (AuthHttp): AuthHttp instance. (TODO: wanted to use type
     *         Http, but it turns out AuthHttp isn't a proper subclass of Http)
     * Returns:
     *      void
     */
    static downloadFile(url: string, authHttp: AuthHttp): Observable<string> {
        let headers = new Headers({
            'Accept': 'application/octet-stream'
        });
        let options = new RequestOptions({
            headers: headers,
            responseType: ResponseContentType.Blob
        });
        let observable: Observable <string> = Observable.create(function subscribe(observer: Observer<string>) {
            observer.next('start');    
            try {
                let requestStream = authHttp.get(url, options);
                requestStream.subscribe(
                    res => {
                        let disposition = res.headers.get('Content-Disposition');
                        let filename = disposition.split('filename=', 2)[1];
                        saveAs(res.blob(), filename);
                        observer.complete();
                    });
            } catch (err) {
                observer.error(err);
            };
        });
        return observable;
    }
}