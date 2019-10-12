import {AuthHttp} from 'angular2-jwt';
import {Observable} from 'rxjs/Observable';

import 'rxjs/add/operator/concat';
import 'rxjs/add/operator/toArray';

/**
 * This class provides methods for working with Eve endpoints.
 */
export class EveUtilities {

    /**
     * Given a URL for a paginated Eve endpoint, returns an Observable that'll
     * gather all items in the collection into a single array.
     *
     * Args:
     *     url (string): URL for a paginated Eve endpoint.
     *     authHttp (AuthHttp): AuthHttp instance. (TODO: wanted to use type
     *         Http, but it turns out AuthHttp isn't a proper subclass of Http)
     * Returns:
     *      Observable<any[]> that'll publish a single array containing all of
     *      the items in the collection.
     */
    static getAllItems(url: string, authHttp: AuthHttp): Observable<any[]> {
        return EveUtilities.getPagesRecursively(url, 1, authHttp).toArray();
    }

    /**
     * Given a URL for a paginated Eve endpoint and a page number, returns an
     * Observable that'll stream all items from the page and subsequent pages.
     * Callers outside the EveUtilities class will typically want to use
     * the above `getAllItems` method instead.
     *
     * Args:
     *     url (string): URL for a paginated Eve endpoint.
     *     authHttp (AuthHttp): AuthHttp instance. (TODO: wanted to use type
     *         Http, but it turns out AuthHttp isn't a proper subclass of Http)
     *     page (number): Page number; note the first page of Eve results is 1,
     *         not 0.
     * Returns:
     *      Observable<any> that'll publish one object per item on the page and
     *      all following pages, until the last page is reached.
     */
    static getPagesRecursively(url: string, page: number, authHttp: AuthHttp): Observable<any> {
        var separator: string = url.indexOf('?') == -1 ? "?" : "&";
        var pagedUrl: string = url + separator + "page=" + page;
        return authHttp
            .get(pagedUrl)
            .flatMap((response: any) => {
                var data = response.json();
                var meta: any = data._meta;
                var items: any[] = data._items;
                var itemStream: Observable<any> = Observable.from(items);
                if (meta.page < meta.last_page) {
                    itemStream = itemStream.concat(EveUtilities.getPagesRecursively(url, page+1, authHttp));
                }
                return itemStream;
            }
        );
    }
}
