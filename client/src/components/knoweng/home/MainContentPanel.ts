import {Component, OnInit} from '@angular/core';
import {SessionService} from '../../../services/common/SessionService';

@Component({
    moduleId: module.id,
    selector: 'main-content-panel',
    templateUrl: './MainContentPanel.html',
    styleUrls: ['./MainContentPanel.css']
})

export class MainContentPanel implements OnInit {
    class = 'relative';
    
    displayName: string = "";
    constructor(
        private _sessionService: SessionService) {

        this.displayName = this._sessionService.getDisplayName();
    }
    ngOnInit() {
    }
}
