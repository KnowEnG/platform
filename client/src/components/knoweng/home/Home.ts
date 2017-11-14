import {Component, OnInit} from '@angular/core';

@Component({
    moduleId: module.id,
    selector: 'home',
    templateUrl: './Home.html',
    styleUrls: ['./Home.css']
})

export class Home implements OnInit {
    class = 'relative';
    constructor() {
    }
    
    ngOnInit() {
    }
}
