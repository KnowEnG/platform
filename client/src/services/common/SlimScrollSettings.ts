import {Injectable} from '@angular/core';

/** This service is a simple shared wrapper for the ISlimScrollSettings passed into several modules */
@Injectable()
export class SlimScrollSettings {
  // TODO: Source these from CSS somehow? 
  // These feel like settings that belong there
  // see ISlimScrollOptions for all options
  private settings: any = {
    position: 'right',
    barBackground: '#152A3C',
    gridWidth: '6',
    gridMargin: '1px 2px;',
    barWidth: '5',
    barOpacity: '0.65'
  };

  get() {
    return this.settings;
  }
}