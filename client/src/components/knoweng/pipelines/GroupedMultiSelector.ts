import {Component, Input, OnChanges, SimpleChange} from '@angular/core';

import {FormData, SelectFormField, SelectOption} from '../../../models/knoweng/Form';

@Component ({
    moduleId: module.id,
    selector: 'grouped-multi-selector',
    styleUrls: ['./GroupedMultiSelector.css'],
    templateUrl: './GroupedMultiSelector.html'
})

export class GroupedMultiSelector implements OnChanges {
    class = 'relative';

    @Input()
    selectFormField: SelectFormField;

    @Input()
    formData: FormData;

    groups: OptionGroup[] = [];
    constructor() {
    }

    /** Handles updates to the inputs. */
    ngOnChanges(changes: {[propertyName: string]: SimpleChange}) {
        this.groups = this.selectFormField.getGroupNames().map((groupName: string) => new OptionGroup(
            groupName, false, this.selectFormField.options.filter((option: SelectOption) => option.group == groupName)));
        // remove any groups that don't contain enabled options
        this.groups = this.groups.filter((group: OptionGroup) => group.options.length > 0);
        if (this.groups.length > 0)
            //open the first group (super collection) by default
            this.groups[0].open = true;
    }
    toggleGroup(toggled: OptionGroup): void {
        this.groups.forEach((group: OptionGroup) => {
            if (group === toggled) {
                group.open = !group.open;
            } else {
                group.open = false;
            }
        })
    }
    getCurrentIcon(isOpen: boolean): string {
        return isOpen ? 'img/knoweng/collection-open.svg' : 'img/knoweng/collection-close.svg';
    }
}

class OptionGroup {
    constructor(
        public name: string,
        public open: boolean,
        public options: SelectOption[]) {
    }
    getTotalOptionsCount(): number {
        return this.options.length;
    }
    getSelectedOptionsCount(): number {
        return this.options.filter((option: SelectOption) => option.selected).length;
    }
    onAllClicked(): void {
        // store current counts to local variables (overkill for current number of cases handled below, but maybe we'll want more cases)
        let currentTotal: number = this.getTotalOptionsCount();
        let currentSelected: number = this.getSelectedOptionsCount();
        if (currentTotal == currentSelected) {
            // all are selected; deselect all
            this.options.forEach((option: SelectOption) => option.selected = false);
        } else {
            // select all
            this.options.forEach((option: SelectOption) => option.selected = true);
        }
    }
}