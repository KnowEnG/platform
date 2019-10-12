import {Injectable} from '@angular/core';
import {BehaviorSubject} from 'rxjs/BehaviorSubject';

@Injectable()
export class ThresholdPickerService {

     // TODO what'll give us our first value? derive from analytics?
    numIncludedStream: BehaviorSubject<number> = new BehaviorSubject<number>(10);

    constructor() {
    }
}
