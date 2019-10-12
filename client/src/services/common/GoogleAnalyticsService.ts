import {Injectable} from "@angular/core";

/**
 * A simple Angular service for tracking Angular events with Google Analytics.
 * 
 * Prerequisites:
 *    - npm install --save-dev @types/google.analytics
 *    - Include <script> Tracking Code from Google Analytics in your index.html
 * 
 * Source: https://blog.thecodecampus.de/angular-2-include-google-analytics-event-tracking/
 * 
 */
@Injectable()
export class GoogleAnalyticsService {
 
  /**  
   * Emits a Custom Event to Google Analytics, indicating that an active user 
   * has performed a particular action.
   */
  public emitEvent(eventCategory: string,
                   eventAction: string,
                   eventLabel: string = null,
                   eventValue: number = null) {
    ga('send', 'event', {
      eventCategory: eventCategory,
      eventLabel: eventLabel,
      eventAction: eventAction,
      eventValue: eventValue
    });
  }
  
  /**  
   * Emits a "Page View" Event to Google Analytics, indicating that an
   * active user has activated a particular route.
   */
  public emitPageView(url: string) {
    ga('set', 'page', url);
    ga('send', 'pageview');
  }
}