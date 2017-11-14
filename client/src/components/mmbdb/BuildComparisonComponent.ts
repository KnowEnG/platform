import {Component} from '@angular/core';
import {CanActivate} from '@angular/router';
import {tokenNotExpired} from 'angular2-jwt';

@Component({
    moduleId: module.id,
    selector: 'build-comparison',
    styleUrls: ['./CohortComparisonTool.css'],
    template: `
        <div>
            <div class="tab-comparison">
                Comparison 1
            </div>
        </div>
        <div class="row-cohorts-otu-picker">
            <div class="row-cohorts">
                <div class="row-cohorts-item">
                    <p class="title-cohort">
                        Baseline Cohort
                    </p>
                    <button type="button" class="btn button-cohort baseline-bg-color">
                        Woman, Healthy,<br>
                        Age: 30-40, <br>
                        Diet: Meat Eater
                    </button>
                </div><!-- no whitespace outside comments between inline-block elements

             --><div class="row-cohorts-item">
                    <p class="title-cohort">
                        Cohort 1
                    </p>
                    <button type="button" class="btn button-cohort cohort1-bg-color">
                         Woman, Has Crohn's,<br>
                        Age: 30-40, <br>
                        Diet: Meat Eater
                    </button>
                </div><!-- no whitespace outside comments between inline-block elements

             --><div class="row-cohorts-item">
                    <p class="title-cohort">
                        Individual Sample
                    </p>
                    <button type="button" class="btn button-cohort mockup-individual">
                        optional
                    </button>
                </div>
            </div>
            <div class="run-analysis-container">
                <button type="button" class="btn button-run-analysis">
                        Run Comparison Analysis
                </button>
            </div>
            <div class="mockup-empty">
            </div>
        </div>
    `
})

export class BuildComparisonComponent {
    class = 'relative';
}