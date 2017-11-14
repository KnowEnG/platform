import {Component, HostListener} from '@angular/core';

import {SessionService} from '../../services/common/SessionService';
import {FileUploadService} from '../../services/knoweng/FileUploadService';

@Component({
    moduleId: module.id,
    selector: 'authorized-user-app',
    templateUrl: './AuthorizedUserApp.html',
    styleUrls: ['./AuthorizedUserApp.css']
})

export class AuthorizedUserApp {
    class = 'relative';
    
    displayName: string = "";
    thumbnailUrl: string = "";
    constructor(
        private _sessionService: SessionService,
        private _fileUploadService: FileUploadService) {

        this.displayName = this._sessionService.getDisplayName();

        var thumb: string = this._sessionService.getThumbnailUrl();
        this.thumbnailUrl = (thumb === null ? 'img/knoweng/profile_thumb.gif' : thumb);
    }
    
    /**
     * https://developer.mozilla.org/en-US/docs/Web/Events/beforeunload, Chrome ignores the custom message in returnValue
     */
    @HostListener('window:beforeunload', ['$event'])
    beforeUnloadHandler($event: any) {
        let queue = this._fileUploadService.getUploaderQueue();
        if (queue.length > 0)
            $event.returnValue="You may not be able to see this because browser has buildin message that can't be customized!";
    }
}
