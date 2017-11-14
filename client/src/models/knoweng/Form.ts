import {HelpContent} from './HelpContent';
import {NestFile} from './NestFile';
import {FileService} from '../../services/knoweng/FileService';

export class Form {
    jobName: string;
    notes: string;
    constructor(
            public label: string,
            public formGroups: FormGroup[]) {
        this.jobName = this.suggestJobName();
        this.notes = "";
    }
    
    setData(formData: FormData): void {
        this.formGroups.forEach((group: FormGroup) => {
            group.fields.forEach((field: FormField) => {
                if (field.isEnabled(formData)) {
                    field.setData(formData);
                }
            });
        });
    }
    getData(): FormData {
        let data: FormDatum[] = [];
        this.formGroups.forEach((group: FormGroup) => {
            group.fields.forEach((field: FormField) => {
                let runningData: FormData = new FormData(data);
                if (field.isEnabled(runningData)) {
                    data = data.concat(field.getData());
                }
            });
        });
        return new FormData(data);
    }
    getSchemaEntries(): SchemaEntry[] {
        let returnVal: SchemaEntry[] = [];
        this.formGroups.forEach((group: FormGroup) => {
            group.fields.forEach((field: FormField) => {
                returnVal = returnVal.concat(field.getSchemaEntries());
            });
        });
        return returnVal;
    }
    suggestJobName(): string {
        // TODO make abstract and improve
        let today: Date = new Date();
        return this.label + "-" + today.getFullYear() + "-" + (today.getMonth()+1) + "-" + today.getDate();
    }
}

// TODO check ng2 final for better way of doing this
export class FormGroup {
    constructor(
        public title: string,
        public helpContent: HelpContent,
        public fields: FormField[]) {
    }
    isValid(formData: FormData): boolean {
        let returnVal: boolean = true;
        this.fields.forEach((field: FormField) => {
            if (field.isEnabled(formData)) {
                returnVal = returnVal && field.isValid();
            }
        });
        return returnVal;
    }
}

export class FormDatum {
    constructor(
        public dbName: string,
        public value: any) {
    }
}

export class FieldSummary {
    constructor(
        public label: string,
        public value: string) {
    }
}

export class SchemaEntry {
    constructor(
        public dbName: string,
        public definition: d3.Map<any>) {
    }
    toString(leadingTabs: number): string {
        return SchemaEntry.levelToString(this.dbName, this.definition, leadingTabs);
    }
    static levelToString(prop: string, dict: d3.Map<any>, leadingTabs: number): string {
        let returnVal: string = "";
        returnVal += "\t".repeat(leadingTabs) + "'" + prop + "': {\n";
        dict.forEach((key: string, value: any) => {
            if (typeof value == "string") {
                returnVal += "\t".repeat(leadingTabs+1) + "'" + key + "': '" + value + "',\n";
            } else if (typeof value == "boolean") {
                returnVal += "\t".repeat(leadingTabs+1) + "'" + key + "': " + (value ? "True" : "False") + ",\n";
            } else if (Array.isArray(value)) {
                let items: string[] = (<string[]>value).map((item: string) => "'" + item + "'");
                returnVal += "\t".repeat(leadingTabs+1) + "'" + key + "': [" + items.join(", ") + "],\n";
            } else if (typeof value == "object") {
                returnVal += SchemaEntry.levelToString(key, value, leadingTabs+1);
            }
        });
        returnVal += "\t".repeat(leadingTabs) + "},\n";
        return returnVal;
    }
}

export class FormData {
    public fieldMap: d3.Map<any> = d3.map<any>();
    constructor(fields: FormDatum[]) {
        fields.forEach((field: FormDatum) => {
            this.fieldMap.set(field.dbName, field.value);
        });
    }
    toFormDatumArray(): FormDatum[] {
        var returnVal: FormDatum[] = [];
        this.fieldMap.forEach((key: string, value: any) => {
            returnVal.push(new FormDatum(key, value));
        });
        return returnVal;
    }
    static fromParametersObject(parameters: any): FormData {
        let fields:FormDatum[] = [];
        for (let key in parameters) {
            if (parameters.hasOwnProperty(key)) {
                fields.push(new FormDatum(key, parameters[key]));
            }
        }
        return new FormData(fields);
    }
}

export type FormPredicate = (formData: FormData) => boolean;
export function IF(field: string, value: any): FormPredicate {
    return (formData) => formData.fieldMap.has(field) && formData.fieldMap.get(field) == value;
}
export function AND(predicates: FormPredicate[]): FormPredicate {
    return (formData) => predicates.every((p) => p(formData));
}
export function OR(predicates: FormPredicate[]): FormPredicate {
    return (formData) => predicates.some((p) => p(formData));
}
export var ALWAYS: FormPredicate = (formData) => true;

export abstract class FormField {
    constructor(
        public isValid: ()=>boolean, // this will change by instance, not just by subclass
        public isEnabled: FormPredicate) { // this will change by instance, not just by subclass
    }
    abstract getData(): FormDatum[];
    abstract setData(formData: FormData): void;
    abstract setDataToDefault(): void;
    abstract isDefault(): boolean;
    abstract getSummary(): FieldSummary[];
    abstract getSchemaEntries(): SchemaEntry[];
}

// only use this on FormField subtypes w/ this.required and a single datum
// could create SingleDatumFormField subtype, but waiting to see what ng2 final has
export function VALID_UNLESS_REQUIRED_BUT_EMPTY(): boolean {
    return (!this.required || (this.getData()[0].value !== null && this.getData()[0].value !== ""));
}

export class SelectFormField extends FormField {
    defaultSelections: boolean[];
    constructor(
        public dbName: string,
        public headline: string,
        public labelNumber: string,
        public label: string,
        public summaryLabel: string,
        public required: boolean,
        public options: SelectOption[],
        public isMultiSelect: boolean,
        public isValid: ()=>boolean,
        public isEnabled: FormPredicate) {
        super(isValid, isEnabled);
        this.defaultSelections = options.map((option) => option.selected);
    }
    getData(): FormDatum[] {
        let returnVal: FormDatum[] = null;
        if (this.isMultiSelect) {
            returnVal = [new FormDatum(this.dbName, this.getSelectedOptions().map((option) => option.value))];
        } else {
            let selected: SelectOption[] = this.getSelectedOptions();
            if (selected.length == 1) {
                returnVal = [new FormDatum(this.dbName, selected[0].value)];
            } else if (selected.length == 0) {
                returnVal = [new FormDatum(this.dbName, null)];
            }
        }
        return returnVal;
    }
    getSelectedOptions(): SelectOption[] {
        return this.options.filter((option) => option.selected);
    }
    setData(formData: FormData) {
        if (formData.fieldMap.has(this.dbName)) {
            var targetValue = formData.fieldMap.get(this.dbName);
            for (var i = 0; i < this.options.length; i++) {
                this.options[i].selected = (targetValue.indexOf(this.options[i].value) != -1);
            }
        } else {
            this.setDataToDefault();
        }
    }
    setDataToDefault(): void {
        for (var i = 0; i < this.options.length; i++) {
            this.options[i].selected = this.defaultSelections[i];
        }
    }
    toggleValue(value: string): void {
        for (var i = 0; i < this.options.length; i++) {
            if (this.options[i].value == value) {
                this.options[i].selected = !this.options[i].selected;
            } else {
                this.options[i].selected = this.isMultiSelect ? this.options[i].selected : false;
            }
        }
    }
    isDefault(): boolean {
        for (var i = 0; i < this.options.length; i++) {
            if (this.options[i].selected != this.defaultSelections[i]) {
                return false;
            }
        }
        return true;
    }
    getGroupNames(): string[] {
        let allGroupNames: string[] = this.options.map((option: SelectOption) => option.group);
        return allGroupNames.filter((element: string, index: number, array: string[]) => array.indexOf(element) == index);
    }
    isGrouped(): boolean {
        return this.getGroupNames().length > 1;
    }
    getGroupOptions(groupName: string): SelectOption[] {
        var groupOptions: SelectOption[] = [];
        var gsoL = d3.nest()
        .key(function(d: SelectOption) { return d.group; })
        .sortValues(function(a: SelectOption, b: SelectOption) {
            if (a.label < b.label) 
                return -1;
            else if (a.label > b.label)
                return 1
            else 
                return 0;
        })
        .entries(this.options);
        gsoL.forEach( function (gso) {
            if (gso.key == groupName) {
                groupOptions = gso.values;
            }
        })
        return groupOptions;
    }
    getSummary(): FieldSummary[] {
        let val: string = null;
        let selected: SelectOption[] = this.getSelectedOptions();
        if (selected.length == 0) {
            val = "";
        } else if (selected.length == 1) {
            val = selected[0].label;
        } else if (this.isGrouped()) {
            // return count per group
            val = this.getGroupNames().map((group: string) => group + ": " + selected.filter((option: SelectOption) => option.group == group).length).join(", ");
        } else {
            val = selected.length + " Selected";
        }
        return [new FieldSummary(this.summaryLabel, val)];
    }
    getSchemaEntries(): SchemaEntry[] {
        var schemaMap: d3.Map<any> = d3.map<any>();
        schemaMap.set("allowed", this.options.map((option: SelectOption) => option.value));
        schemaMap.set("required", this.required);
        if (this.isMultiSelect) {
            schemaMap.set("type", "list");
        } else {
            schemaMap.set("type", "string");
        }
        return [new SchemaEntry(this.dbName, schemaMap)];
    }
}

export class SelectOption {
    constructor(
        public label: string,
        public value: string,
        public selected: boolean,
        public group?: string) { // for now, group is used when isMultiSelect=true to display blocks of options with check all/check none
    }
}

export class NumberFormField extends FormField {
    currentValue: number;
    constructor(
        public dbName: string,
        public headline: string,
        public labelNumber: string,
        public label: string,
        public summaryLabel: string,
        public required: boolean,
        public defaultValue: number,
        public numberType: NumberType,
        public isPercentage: boolean,
        public minimum: number,
        public maximum: number,
        public slider: NumberFormFieldSlider,
        public isValid: ()=>boolean,
        public isEnabled: FormPredicate) {
        super(isValid, isEnabled);
        this.setDataToDefault(); // note Form from Template will need to call setData() on instance
    }
    getData(): FormDatum[] {
        return [new FormDatum(this.dbName, this.currentValue)];
    }
    setData(formData: FormData) {
        if (formData.fieldMap.has(this.dbName)) {
            this.currentValue = formData.fieldMap.get(this.dbName);
        } else {
            this.setDataToDefault();
        }
    }
    setDataToDefault(): void {
        this.currentValue = this.defaultValue;
    }
    isDefault(): boolean {
        return this.currentValue == this.defaultValue;
    }
    getSummary(): FieldSummary[] {
        return [new FieldSummary(this.summaryLabel, this.currentValue + (this.isPercentage ? "%" : ""))];
    }
    getSchemaEntries(): SchemaEntry[] {
        var schemaMap: d3.Map<any> = d3.map<any>();
        schemaMap.set("required", this.required);
        if (this.numberType == NumberType.INTEGER) {
            schemaMap.set("required", "integer");
        } else if (this.numberType == NumberType.FLOAT) {
            schemaMap.set("required", "float");
        } else {
            schemaMap.set("required", "number");
        }
        return [new SchemaEntry(this.dbName, schemaMap)];
    }
}

// only use this on FormField subtypes w/ this.required and a single datum
// could create SingleDatumFormField subtype, but waiting to see what ng2 final has
export function VALID_NUMBER(): boolean {
    var valid = false;
    var value: any = this.getData()[0].value;
    // valid states:
    // 1. value present and it's between min and max
    // 1. value not present and this.required == false
    if (value != null) {
        valid = (this.minimum === null || this.minimum <= value) && (this.maximum === null || value <= this.maximum);
    } else {
        valid = !this.required;
    }
    return valid;
}

export class NumberFormFieldSlider {
    constructor(
        public leftLabel: string,
        public rightLabel: string) {
    }
}

export var SLIDER_NONE: NumberFormFieldSlider = null;
export var SLIDER_NO_LABELS: NumberFormFieldSlider = new NumberFormFieldSlider("", "");

export enum NumberType {INTEGER, FLOAT}

export class BooleanFormField extends FormField {
    currentValue: boolean;
    constructor(
        public dbName: string,
        public headline: string,
        public labelNumber: string,
        public label: string,
        public summaryLabel: string,
        public required: boolean,
        public defaultValue: boolean,
        public isValid: ()=>boolean,
        public isEnabled: FormPredicate) {
        super(isValid, isEnabled);
        this.setDataToDefault(); // note Form from Template will need to call setData() on instance
    }
    getData(): FormDatum[] {
        return [new FormDatum(this.dbName, this.currentValue)];
    }
    setData(formData: FormData) {
        if (formData.fieldMap.has(this.dbName)) {
            this.currentValue = formData.fieldMap.get(this.dbName);
        } else {
            this.setDataToDefault();
        }
    }
    setDataToDefault(): void {
        this.currentValue = this.defaultValue;
    }
    isDefault(): boolean {
        return this.currentValue == this.defaultValue;
    }
    getSummary(): FieldSummary[] {
        return [new FieldSummary(this.summaryLabel, this.currentValue ? "Yes" : "No")];
    }
    getSchemaEntries(): SchemaEntry[] {
        var schemaMap: d3.Map<any> = d3.map<any>();
        schemaMap.set("type", "boolean");
        schemaMap.set("required", this.required);
        return [new SchemaEntry(this.dbName, schemaMap)];
    }
}

// this is a special case because it breaks all the normal rules in the comps:
// - multiple labels inline
// - multiple value widgets occupying the same screen area
// - interactive labels (selecting current value widget)
// trying not to get too fancy about it now
export class DoubleFileFormField extends FormField {
    currentIsFirst: boolean = true;
    constructor(
        public field1: FileFormField,
        public field2: FileFormField
    ) {
        super(
            () => field1.isValid() && field2.isValid(),
            (formData: FormData) => field1.isEnabled(formData) || field2.isEnabled(formData)
        );
        this.setDataToDefault();
    }
    getData(): FormDatum[] {
        return [this.field1.getData()[0], this.field2.getData()[0]];
    }
    setData(formData: FormData) {
        this.field1.setData(formData);
        this.field2.setData(formData);
    }
    setDataToDefault(): void {
        this.currentIsFirst = true;
        this.field1.setDataToDefault();
        this.field2.setDataToDefault();
    }
    isDefault(): boolean {
        return this.field1.isDefault() && this.field2.isDefault();
    }
    getSummary(): FieldSummary[] {
        return [this.field1.getSummary()[0], this.field2.getSummary()[0]];
    }
    getSchemaEntries(): SchemaEntry[] {
        // TODO merge better
        let schema1: SchemaEntry = this.field1.getSchemaEntries()[0];
        let schema2: SchemaEntry = this.field2.getSchemaEntries()[0];
        schema1.definition.set("required", false);
        schema2.definition.set("required", false);
        return [schema1, schema2];
    }
}

export class FileFormField extends FormField {
    currentValue: string;
    constructor(
        public dbName: string,
        public headline: string,
        public labelNumber: string,
        public label: string,
        public summaryLabel: string,
        public required: boolean,
        public defaultValue: string,
        public fileService: FileService,
        public allowUrl: boolean,
        public allowGenePaste: boolean,
        public isValid: ()=>boolean,
        public isEnabled: FormPredicate) {
        super(isValid, isEnabled);
        this.setDataToDefault(); // note Form from Template will need to call setData() on instance
    }
    getData(): FormDatum[] {
        return [new FormDatum(this.dbName, this.currentValue)];
    }
    setData(formData: FormData) {
        if (formData.fieldMap.has(this.dbName)) {
            this.currentValue = formData.fieldMap.get(this.dbName);
        } else {
            this.setDataToDefault();
        }
    }
    setDataToDefault(): void {
        this.currentValue = this.defaultValue;
    }
    isDefault(): boolean {
        return this.currentValue == this.defaultValue;
    }
    getSummary(): FieldSummary[] {
        // summary value is null for no selection, undefined for unrecognized selection
        let summaryValue: string = null;
        if (this.currentValue) {
            let currentId = parseInt(this.currentValue, 10);
            let match: NestFile = this.fileService.getFileByIdSync(currentId);
            if (match !== undefined) {
                summaryValue = match.filename;
            } else {
                summaryValue = undefined;
            }
        }
        return [new FieldSummary(this.summaryLabel, summaryValue)];
    }
    getSchemaEntries(): SchemaEntry[] {
        var schemaMap: d3.Map<any> = d3.map<any>();
        schemaMap.set("type", "objectid");
        schemaMap.set("required", this.required);
        var relationMap: d3.Map<any> = d3.map<any>();
        relationMap.set("resource", "files");
        relationMap.set("field", "_id");
        relationMap.set("embeddable", true);
        schemaMap.set("data_relation", relationMap);
        return [new SchemaEntry(this.dbName, schemaMap)];
    }
}

export class TextboxFormField extends FormField {
    currentValue: string;
    constructor(
        public dbName: string,
        public headline: string,
        public labelNumber: string,
        public label: string,
        public summaryLabel: string,
        public required: boolean,
        public defaultValue: string,
        public isValid: ()=>boolean,
        public isEnabled: FormPredicate) {
        super(isValid, isEnabled);
        this.setDataToDefault(); // note Form from Template will need to call setData() on instance
    }
    getData(): FormDatum[] {
        return [new FormDatum(this.dbName, this.currentValue)];
    }
    setData(formData: FormData) {
        if (formData.fieldMap.has(this.dbName)) {
            this.currentValue = formData.fieldMap.get(this.dbName);
        } else {
            this.setDataToDefault();
        }
    }
    setDataToDefault(): void {
        this.currentValue = this.defaultValue;
    }
    isDefault(): boolean {
        return this.currentValue == this.defaultValue;
    }
    getSummary(): FieldSummary[] {
        return [new FieldSummary(this.summaryLabel, this.currentValue)];
    }
    getSchemaEntries(): SchemaEntry[] {
        var schemaMap: d3.Map<any> = d3.map<any>();
        schemaMap.set("type", "objectid");
        schemaMap.set("required", this.required);
        var relationMap: d3.Map<any> = d3.map<any>();
        relationMap.set("resource", "files");
        relationMap.set("field", "_id");
        relationMap.set("embeddable", true);
        schemaMap.set("data_relation", relationMap);
        return [new SchemaEntry(this.dbName, schemaMap)];
    }
}

// this is another special case:
// - multiple labels inline
// - multiple value widgets occupying the same screen area
// - interactive labels
// trying not to get too fancy about it now
export class TextboxOrFileFormField extends FormField {
    private currentIsFile: boolean;
    constructor(
        public required: boolean,
        public headline: string,
        public labelNumber: string,
        public defaultIsFile: boolean,
        public textboxField: TextboxFormField,
        public fileField: FileFormField) {
        super(
            () => fileField.isValid() || textboxField.isValid(),
            (formData: FormData) => fileField.isEnabled(formData) || textboxField.isEnabled(formData)
        );
        this.setDataToDefault();
    }
    getCurrentIsFile(): boolean {
        return this.currentIsFile;
    }
    setCurrentIsFile(newVal: boolean): void {
        this.currentIsFile = newVal;
        if (this.currentIsFile) {
            this.textboxField.currentValue = null;
        } else {
            this.fileField.currentValue = null;
        }
    }
    getData(): FormDatum[] {
        let returnVal: FormDatum[] = null;
        if (this.currentIsFile) {
            returnVal = this.fileField.getData();
        } else {
            returnVal = this.textboxField.getData();
        }
        return returnVal;
    }
    setData(formData: FormData) {
        this.fileField.setData(formData);
        this.textboxField.setData(formData);
    }
    setDataToDefault(): void {
        this.currentIsFile = this.defaultIsFile;
        this.textboxField.setDataToDefault();
        this.fileField.setDataToDefault();
    }
    isDefault(): boolean {
        return this.currentIsFile == this.defaultIsFile && (
            (this.currentIsFile && this.fileField.isDefault()) ||
            (!this.currentIsFile && this.textboxField.isDefault()));
    }
    getSummary(): FieldSummary[] {
        let returnVal: FieldSummary[] = null;
        if (this.currentIsFile) {
            returnVal = this.fileField.getSummary();
        } else {
            returnVal = this.textboxField.getSummary();
        }
        return returnVal;
    }
    getSchemaEntries(): SchemaEntry[] {
        // TODO merge better
        let schema1: SchemaEntry = this.fileField.getSchemaEntries()[0];
        let schema2: SchemaEntry = this.textboxField.getSchemaEntries()[0];
        schema1.definition.set("required", false);
        schema2.definition.set("required", false);
        return [schema1, schema2];
    }
}

export class HiddenFormField extends FormField {
    currentValue: string;
    constructor(
        public dbName: string,
        public defaultValue: string,
        public isEnabled: FormPredicate) {
        super(VALID_UNLESS_REQUIRED_BUT_EMPTY, isEnabled);
        this.setDataToDefault(); // note Form from Template will need to call setData() on instance
    }
    getData(): FormDatum[] {
        return [new FormDatum(this.dbName, this.currentValue)];
    }
    setData(formData: FormData) {
        if (formData.fieldMap.has(this.dbName)) {
            this.currentValue = formData.fieldMap.get(this.dbName);
        } else {
            this.setDataToDefault();
        }
    }
    setDataToDefault(): void {
        this.currentValue = this.defaultValue;
    }
    isDefault(): boolean {
        return this.currentValue == this.defaultValue;
    }
    getSummary(): FieldSummary[] {
        return [new FieldSummary(this.dbName, this.currentValue)];
    }
    getSchemaEntries(): SchemaEntry[] {
        var schemaMap: d3.Map<any> = d3.map<any>();
        schemaMap.set("type", "string");
        schemaMap.set("required", false);
        return [new SchemaEntry(this.dbName, schemaMap)];
    }
}
