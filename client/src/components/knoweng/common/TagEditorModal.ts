import {Component, OnInit, EventEmitter, Output, Input} from '@angular/core';

@Component({
    moduleId: module.id,
    selector: 'tag-editor-modal',
    templateUrl: './TagEditorModal.html',
    styleUrls: ['./TagEditorModal.css']
})

export class TagEditorModal implements OnInit {
    class = 'relative';
    
    @Input()
    initialTags: Tag[];

    @Output()
    done: EventEmitter<Tag[]> = new EventEmitter<Tag[]>();

    currentTags: Tag[];

    constructor() {
    }
    ngOnInit() {
        // clone
        this.currentTags = this.initialTags.map((tag) => (<Tag>{name: tag.name, applied: tag.applied}) );
        this.sortTags();
    }
    sortTags() {
        this.currentTags.sort((a, b) => {
            if (a.applied && !b.applied) {
                return -1;
            }
            if (b.applied && !a.applied) {
                return 1;
            }
            var aName: string = a.name.toLowerCase();
            var bName: string = b.name.toLowerCase();
            return ( ( aName == bName ) ? 0 : ( ( aName > bName ) ? 1 : -1 ) );
        });
    }
    onKeyup(event: Event) {
        if ((<any>event).which == 13) {
            // user pressed enter; add the tag
            this.currentTags.push({name: (<any>event.target).value.trim(), applied: true});
            this.sortTags();
            (<any>event.target).value = "";
        }
    }
    onRemove(tag: Tag) {
        tag.applied = false;
        this.sortTags();
    }
    onDone() {
        this.done.emit(this.currentTags);
    }
}

export interface Tag {
    name: string;
    applied: boolean;
}