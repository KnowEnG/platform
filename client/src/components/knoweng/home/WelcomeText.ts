import {Component, OnInit} from '@angular/core';

@Component({
    moduleId: module.id,
    selector: 'welcome-text',
    templateUrl: './WelcomeText.html',
    styleUrls: ['./WelcomeText.css', '../common/SupportAndWelcomeText.css']
})

export class WelcomeText implements OnInit {
    class = 'relative';
    
    constructor() {
    }
    ngOnInit() {
    }
}
