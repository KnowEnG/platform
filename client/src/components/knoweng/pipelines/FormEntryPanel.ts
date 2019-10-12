import {Component, OnInit, OnChanges, SimpleChange, Input, ChangeDetectorRef} from '@angular/core';

import {Form, FormData, FormField, SelectFormField, SelectOption, BooleanFormField, NumberFormField, FileFormField, HiddenFormField} from '../../../models/knoweng/Form';
import {LogService} from '../../../services/common/LogService';

import {Pipeline} from '../../../models/knoweng/Pipeline';

@Component({
    moduleId: module.id,
    selector: 'form-entry-panel',
    templateUrl: './FormEntryPanel.html',
    styleUrls: ['./FormEntryPanel.css']
})

export class FormEntryPanel implements OnInit, OnChanges {
    class = 'relative';

    @Input()
    currentIndex: number;

    @Input()
    form: Form = null; // defines forms and provides help content

    @Input()
    pipeline: Pipeline = null; // defines forms and provides help content

    formData: FormData;

    constructor(private logger: LogService,
                private changeRef: ChangeDetectorRef) {
    }

    ngOnInit() {
        this.formData = this.form.getData();
    }
    
    ngOnChanges(changes: {[propertyName: string]: SimpleChange}) {
    }
    
    setCurrentPageToDefault(): void {
        this.form.formGroups[this.currentIndex].fields.forEach(field => field.setDataToDefault());
        this.formData = this.form.getData();
    }
    
    getFieldType(field: FormField, log: boolean = false): string {
        var returnVal: string = null;
        if (field instanceof SelectFormField) {
            if (field.isMultiSelect) {
                if (field.isGrouped()) {
                    returnVal = "grouped-multi-select";
                } else {
                    returnVal = "flat-multi-select";
                }
            } else {
                if(field.isGrouped()) {
                    returnVal = "grouped-select";
                } else {
                    returnVal = "select";
                }
            }
        } else if (field instanceof BooleanFormField) {
            returnVal = "boolean";
        } else if (field instanceof NumberFormField) {
            returnVal = "number";
        } else if (field instanceof FileFormField) {
            returnVal = "file";
        } else if (field instanceof HiddenFormField) {
            returnVal = "hidden";
        }
        if (log) {
            this.logger.info("returning " + returnVal + " in getFieldType");
            this.logger.info(JSON.stringify(field));
        }
        return returnVal;
    }
}
