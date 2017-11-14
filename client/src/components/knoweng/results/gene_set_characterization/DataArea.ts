import {Component, OnInit, Input} from '@angular/core';

import {ComparisonGeneSet, UserGeneSet, Result} from '../../../../models/knoweng/results/GeneSetCharacterization';

import {Job} from '../../../../models/knoweng/Job';

@Component({
    moduleId: module.id,
    selector: 'gsc-data-area',
    templateUrl: './DataArea.html',
    styleUrls: ['./DataArea.css']
})

export class DataArea implements OnInit {
    class = 'relative';

    @Input()
    job: Job;

    @Input()
    gradientMaxColor: string;

    @Input()
    gradientMinColor: string;

    @Input()
    gradientMaxThreshold: number;

    @Input()
    gradientMinThreshold: number;

    @Input()
    gradientCurrentThreshold: number;

    @Input()
    comparisonGeneSets: ComparisonGeneSet[];

    @Input()
    selectedUserGeneSets: UserGeneSet[];

    @Input()
    selectedComparisonGeneSets: ComparisonGeneSet[];

    @Input()
    result: Result;

    /** one of heatmap, network, spreadsheet, job */
    activeTab: string = 'heatmap';

    constructor() {
    }
    ngOnInit() {
    }
}
