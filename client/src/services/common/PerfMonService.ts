import {Injectable} from '@angular/core';
import {LogService} from './LogService';

@Injectable()
export class PerfMonService {
  constructor(private _logger: LogService) {
  }
  
  /*
   * !!!! DEBUG ONLY !!!!   This function should not be called from production code.
   * Returns the current size of the client's JavaScript heap as a number in MB.
   *
   *    NOTE: For this service to work, you must start Chrome with the "--enable-precise-memory-info" flag
   *    See http://stackoverflow.com/questions/25389096/why-is-memory-usage-not-correctly-updated
   *
   * Example Performance object:
   *   performance: Performance
   *      memory: MemoryInfo
   *         jsHeapSizeLimit: 1530000000
   *         totalJSHeapSize: 139000000
   *         usedJSHeapSize: 97400000
   *      onresourcetimingbufferfull: null
   *      onwebkitresourcetimingbufferfull: null
   *      navigation: PerformanceNavigation
   *         redirectCount: 0
   *         type: 1
   *      timing: PerformanceTiming
   *         connectEnd: 1491427198354
   *         connectStart: 1491427198354
   *         domComplete: 1491427199671
   *         domContentLoadedEventEnd: 1491427199409
   *         domContentLoadedEventStart: 1491427199406
   *         domInteractive: 1491427199406
   *         domLoading: 1491427198427
   *         domainLookupEnd: 1491427198354
   *         domainLookupStart: 1491427198354
   *         fetchStart: 1491427198354
   *         loadEventEnd: 1491427199685
   *         loadEventStart: 1491427199671
   *         navigationStart: 1491427198354
   *         redirectEnd: 0
   *         redirectStart: 0
   *         requestStart: 1491427198365
   *         responseEnd: 1491427198422
   *         responseStart: 1491427198419
   *         secureConnectionStart: 0
   *         unloadEventEnd: 1491427198422
   *         unloadEventStart: 1491427198422
   *         
   * 
   */
  heapSize(): number {
    var perf = (<any> performance);
    if (!perf.memory) {
        this._logger.error('!!! performance.memory not supported !!!');
        return -1;
    }
    if (!perf.memory.usedJSHeapSize) {
        this._logger.error('!!! performance.memory.usedJSHeapSize not supported !!!');
        return -1;
    }
    let raw: number = perf.memory.usedJSHeapSize;
    let size: number = Math.round(raw / 10000) / 100;
    this._logger.info('Used JSHeapSize (MB): ' + size + ", raw: " + raw.toString());
    return size;
  };
};