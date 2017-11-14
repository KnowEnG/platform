import {Component} from '@angular/core';
import {CanActivate} from '@angular/router';
import {tokenNotExpired} from 'angular2-jwt';

@Component ({
    moduleId: module.id,
    selector: 'getting-started',
    templateUrl: './GettingStartedComponent.html',
    styleUrls: ['./GettingStartedComponent.css']
})

export class GettingStartedComponent {
    class = 'relative';
}