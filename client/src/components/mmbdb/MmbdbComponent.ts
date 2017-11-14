import {Component, OnInit} from '@angular/core';
import {Router} from '@angular/router';

import {SessionService} from '../../services/common/SessionService';
import {Cohort, Comparison} from '../../models/mmbdb/CohortComparison';
import {CohortComparisonService} from '../../services/mmbdb/CohortComparisonService';

@Component({
    moduleId: module.id,
    selector: 'mmbdb-app',
    templateUrl: './MmbdbComponent.html',
    styleUrls: ['./MmbdbComponent.css'],
    providers: [CohortComparisonService]
})

export class MmbdbComponent implements OnInit{
    class = 'relative';
    
    sidenavCollapsed: boolean = false;
    // TODO create new component for what are now .side-menu-items, and
    // the can track their own collapsed states
    // will require ng-content for .side-menu-item-body contents
    cohortsCollapsed: boolean = true;
    individualsCollapsed: boolean = true;
    comparisonsCollapsed: boolean = false;
    reportsCollapsed: boolean = true;

    userDisplayName: string = "";
    
    cohorts: Cohort[];
    individuals: Cohort[];
    
    comparisons: Comparison[];
    
    toggleSidenavCollapsed(): void {
        this.sidenavCollapsed = !this.sidenavCollapsed;
    }
    
    constructor(
        private _router: Router,
        private _sessionService: SessionService,
        public cohortComparisonService: CohortComparisonService) {
        this.checkSession();
        var givenName: string = this._sessionService.getGivenName();
        var familyName: string = this._sessionService.getFamilyName();
        this.userDisplayName =
            (givenName === null ? "" : givenName + " ") +
            (familyName === null ? "" : familyName);
    }
    
    isRouteActive(path: string): boolean {
        var isActive: boolean = this._router.isActive(this._router.createUrlTree([path]), true);
        return isActive;
    }
    
    checkSession() {
        if (!this._sessionService.hasValidSession()) {
            this._sessionService.redirectToLogin();
        }
    }
    
    ngOnInit() {
        this.cohortComparisonService.getCohorts()
            .subscribe((cohorts: Cohort[]) => {
                this.cohorts = cohorts.filter((cohort) => cohort.num_samples != 1);
                this.individuals = cohorts.filter((cohort) => cohort.num_samples == 1);
            });
        this.cohortComparisonService.getComparisons()
            .subscribe((comparisons: Comparison[]) => {
                this.comparisons = comparisons;
            });
    }
}