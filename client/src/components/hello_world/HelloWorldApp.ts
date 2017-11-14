import {platformBrowserDynamic} from '@angular/platform-browser-dynamic';

import {HelloWorldModule} from './HelloWorldModule';



platformBrowserDynamic().bootstrapModule(HelloWorldModule)
    .catch((err: any) => console.error(err));

