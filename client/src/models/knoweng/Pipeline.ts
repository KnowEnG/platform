import {Observable} from 'rxjs/Observable';

import {HelpContent} from './HelpContent';
import {Form} from './Form';

export class Pipeline {
    constructor(
        public title: string,
        public slug: string,
        public description: string,
        public overview: HelpContent,
        public getForm: ()=>Observable<Form>) {
    }
}
