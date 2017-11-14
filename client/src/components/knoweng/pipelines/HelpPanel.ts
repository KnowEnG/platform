import {Component, Input, OnChanges, SimpleChange} from '@angular/core';
import {ISlimScrollOptions} from 'ng2-slimscroll';

import {HelpContent, HelpContentGroup, HelpContentElement, HelpElementType} from '../../../models/knoweng/HelpContent';
import {SlimScrollSettings} from '../../../services/common/SlimScrollSettings';

@Component ({
    moduleId: module.id,
    selector: 'help-panel',
    styleUrls: ['./HelpPanel.css'],
    templateUrl: './HelpPanel.html'
})

export class HelpPanel implements OnChanges {
    class = 'relative';
    
    public slimScrollOpts: ISlimScrollOptions;
    
    @Input()
    height: number = 0;

    @Input()
    content: HelpContent = null;

    collapsed: boolean = false;

    openGroupIndex: number = null;
    
    /* these simplify life in the template */
    heading: HelpElementType = HelpElementType.HEADING;
    body: HelpElementType = HelpElementType.BODY;

    constructor(private _scrollSettings: SlimScrollSettings) {
    }
    ngOnInit() {
        // check ISlimScrollOptions for all options
        // FIXME: this is currently unused (see template)
        this.slimScrollOpts = this._scrollSettings.get();
    }
    /** Handles updates to the inputs. */
    ngOnChanges(changes: {[propertyName: string]: SimpleChange}) {
        this.openGroupIndex = 0;
    }
    onCollapse() {
        this.collapsed = true;
    }
    onExpand() {
        this.collapsed = false;
    }
    toggleOpenGroup(index: number): void {
        if (index == this.openGroupIndex) {
            this.openGroupIndex = null;
        } else {
            this.openGroupIndex = index;
        }
    }
}
