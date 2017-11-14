import {Component} from '@angular/core';
import {CanActivate} from '@angular/router';
import {tokenNotExpired} from 'angular2-jwt'

@Component({
    selector: 'create-reports',
    template: '<h3 style="color: #ffffff"> Reports will be created here...</h3>'
})

export class CreateReportsComponent {
    
}
