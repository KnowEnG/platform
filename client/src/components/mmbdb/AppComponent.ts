import {Component} from '@angular/core';
import {HashLocationStrategy, LocationStrategy} from '@angular/common';

@Component({
    selector: 'app',
    template: `
        <div>
            <router-outlet></router-outlet>
        </div>
    `,
    providers: [
            {provide: LocationStrategy, useClass: HashLocationStrategy}
        ]
})

export class AppComponent {
    
}