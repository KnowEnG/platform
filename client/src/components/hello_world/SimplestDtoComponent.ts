import {Component} from '@angular/core';
import {Http, Response} from '@angular/http';

@Component({
  selector: 'simplest-dto',
  template: `
  <h2>Basic Request</h2>
  <button type="button" (click)="makeRequest()">Read Simplest DTO</button>
  <pre *ngIf='data'>{{data | json}}</pre>
`
})

export class SimplestDtoComponent {
    data: Object;

    constructor(public http: Http) {
    }

    makeRequest(): void {
        this.http.request('/api/simplest_dto')
            .subscribe((res: Response) => {
                this.data = res.json();
        });
    }
}