import {Injectable} from '@angular/core';
import {Response} from '@angular/http';
import {AuthHttp} from 'angular2-jwt';
import {Observable} from 'rxjs/Observable';
import {BehaviorSubject} from 'rxjs/BehaviorSubject';

import {Species, Collection, AnalysisNetwork} from '../../models/knoweng/KnowledgeNetwork';
import {LogService} from '../common/LogService';
import {SessionService} from '../common/SessionService';

@Injectable()
export class KnowledgeNetworkService {

    private _speciesUrl: string = '/api/v2/species';
    private _collectionUrl: string = '/api/v2/collections';
    private _analysisNetworkUrl: string = '/api/v2/analysis_networks';
    
    // a stream of the current Species[], initialized to []
    private _speciesSubject: BehaviorSubject<Species[]> = new BehaviorSubject<Species[]>([]);
    
    constructor(private authHttp: AuthHttp, private logger: LogService, private sessionService: SessionService) {
        //fetching species does not depend on user input so we will just perform http get once here
        this.sessionService.tokenChanged()
            .subscribe(
                data => this.fetchSpecies(),
                err => this.logger.error("KNService failed to refresh token")
            );
    }

    /**
     * Returns a stream of the current Species[]
     */
    getSpecies(): Observable<Species[]> {
         return this._speciesSubject.asObservable();
    }
     
    /**
     * Helper function that actually performs HTTP GET on species
     */
    fetchSpecies() {
        var requestStreamS = this.authHttp
            .get(this._speciesUrl)
            .map(res => {
                let speciesData: any[] = res.json()._items;
                return speciesData.map((speciesDatum: any) => new Species(
                    speciesDatum._id,
                    speciesDatum.name,
                    speciesDatum.short_latin_name,
                    speciesDatum.species_number,
                    speciesDatum.group_name,
                    speciesDatum.display_order,
                    speciesDatum.selected_by_default)); 
            });
        requestStreamS.subscribe(
            sArr => {
                this._speciesSubject.next(sArr);
            },
            err => {
                this.logger.error("Failed fetching species data");
            }
        );
    }
    
    /**
     * Returns a stream of the current Collection[]
     */
    getCollections(speciesNumber: string): Observable<Collection[]> {
        let query = '?';
        if (speciesNumber !== null) {
            query += 'species_number=' + speciesNumber + '&';
        }
        query += 'sort=super_collection_display_index,collection'
        return this.authHttp
            .get(this._collectionUrl + query)
            .map(res => {
                return res.json()._items.map((collectionDatum: any) => new Collection(
                    collectionDatum._id,
                    collectionDatum.super_collection,
                    collectionDatum.species_number,
                    collectionDatum.edge_type_name,
                    collectionDatum.super_collection_display_index,
                    collectionDatum.collection,
                    collectionDatum.collection_selected_by_default));
            });
    }
    
    /**
     * Returns a stream of the current AnalysisNetwork[]
     */
    getAnalysisNetworks(speciesNumber: string): Observable<AnalysisNetwork[]> {
        let query = '';
        if (speciesNumber !== null) {
            query = '?species_number=' + speciesNumber;
        }
        return this.authHttp
            .get(this._analysisNetworkUrl + query)
            .map(res => {
                return res.json()._items.map((networkDatum: any) => new AnalysisNetwork(
                    networkDatum._id,
                    networkDatum.analysis_network_name,
                    networkDatum.species_number,
                    networkDatum.edge_type_name,
                    networkDatum.selected_by_default));
            });
    }
}
