import {Component, Input, OnInit, OnDestroy} from '@angular/core';
import {Http, Headers, Response} from '@angular/http';
import {Router} from '@angular/router';
import {Observable} from 'rxjs/Observable';
import {Subscription} from 'rxjs/Subscription';

import {NestFile} from '../../../models/knoweng/NestFile';
import {FileService} from '../../../services/knoweng/FileService';
import {SessionService} from '../../../services/common/SessionService';
import {LogService} from '../../../services/common/LogService';

@Component({
    moduleId: module.id,
    selector: 'manuscript-support',
    templateUrl: './ManuscriptSupport.html',
    styleUrls: ['./ManuscriptSupport.css', '../common/SupportAndWelcomeText.css']
})

/**
 * This component is responsible for displaying a dropdown button for user to select a manuscript, as well as reading all user files and manuscripts from system, 
 * and passing the user files and selected manuscript to manuscript child component.  
 */
export class ManuscriptSupport implements OnInit, OnDestroy {
    class = 'relative';
    
    private uploadedFiles: NestFile[];
    private selectedManuscript: Manuscript;
    private manuscriptsUrl = '/static/data/manuscripts.json';
    private manuscripts: Manuscript[];
    
    private fileSub: Subscription;
    
    constructor(private _http: Http,
                private _router: Router,
                private _sessionService: SessionService,
                private _logger: LogService,
                private _fileService: FileService) {
    }
    
    ngOnInit() {
         this.fileSub = this._fileService.getFiles().subscribe(
            (files: Array<NestFile>) => {
                this.uploadedFiles = files.slice().sort((a: NestFile, b: NestFile) => {
                    return d3.ascending(a.filename.toUpperCase(), b.filename.toUpperCase());
                });
                let allFileNames: string[] = [];
                this.uploadedFiles.forEach((file: NestFile) => {
                    allFileNames.push(file.filename);
                });
                //Because file service outputs file list periodically, manuscripts could have been read. In this is the case, 
                //we only need to update data file status for each manuscript. Otherwise we will read manuscripts via HTTP 
                //and default selected manuscript to the first one.
                if (this.manuscripts) {
                    this.manuscripts.forEach((ms: Manuscript) => {
                       let dataFileStatus: boolean = this.getDatafileStatus(allFileNames, ms.dataFiles);
                       if (dataFileStatus != ms.dataLoaded)
                            ms.dataLoaded = dataFileStatus;
                    });
                } else {
                    let headers = new Headers();
                    headers.append('Content-Type', 'application/json');
                    this._http.get(this.manuscriptsUrl, {headers: headers})
                        .map(function (res) {return res.json();})
                        .catch((error: any) => Observable.throw(error))
                        .subscribe((obj: any) => {
                            let manuscripts: Manuscript[]= [];
                            let mts: any[] = obj.manuscripts;
                            mts.forEach(mt =>  {
                                let dataFilesUploaded: boolean = this.getDatafileStatus(allFileNames, mt.data_files)
                                let ms = new Manuscript(
                                    mt.title,
                                    mt.authors,
                                    mt.link,
                                    mt.abstract_sections,
                                    mt.data_files_directory,
                                    mt.data_files,
                                    mt.data_readme_url,
                                    dataFilesUploaded);
                                manuscripts.push(ms);
                            });
                            this.manuscripts = manuscripts;
                            this.selectedManuscript = manuscripts[0];
                        });
                    }
                },
                (error: any) => {
                    if (error.status == 401) {
                        this._sessionService.redirectToLogin();
                    } else {
                        alert(`Server error. Try again later`);
                        this._logger.error(error.message, error.stack);
                    }
                }
            );
    }
     
    ngOnDestroy() {
        this.fileSub.unsubscribe();
    }
    
    selectManuscript(i: number) {
        this.selectedManuscript = this.manuscripts[i];
    }
    
    getDatafileStatus(allFileNames: string[], dataFiles: string[]) {
        let dataFilesUploaded: boolean = true;
        let i: number;
        let num: number = dataFiles.length;
        for (i = 0; i < num; i++) {
            if (!allFileNames.includes(dataFiles[i])) {
                dataFilesUploaded = false;
                break;
            }
        }
        return dataFilesUploaded;
    }
}

export class Manuscript{
    constructor(
        public title: string,
        public authors: string,
        public link: {text: string, url: string},
        public abstractSections: {title: string, text: string}[],
        public dataFilesDirectory: string,
        public dataFiles: string[],
        public dataReadmeUrl: string,
        public dataLoaded: boolean) {
    }
}