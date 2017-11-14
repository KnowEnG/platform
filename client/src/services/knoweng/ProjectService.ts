import {Injectable} from '@angular/core';
import {Headers} from '@angular/http';
import {AuthHttp} from 'angular2-jwt';
import {Observable} from 'rxjs/Observable';
import {BehaviorSubject} from 'rxjs/BehaviorSubject';
import {Subscription} from 'rxjs/Subscription';

import {Project} from '../../models/knoweng/Project';
import {LogService} from '../common/LogService';

@Injectable()
export class ProjectService {

    private _projectUrl: string = '/api/v2/projects';
    // a stream of the current Project[], initialized to []
    private _projectsSubject: BehaviorSubject<Project[]> = new BehaviorSubject<Project[]>([]);

    private _defaultProjectName = 'Default Project';
    
    private tokenSub: Subscription;

    constructor(private authHttp: AuthHttp, private logger: LogService) {
        // as soon as we have an authentication token, or whenever the token
        // changes, fetch data
        this.tokenSub = this.authHttp.tokenStream.subscribe(
            data => this.triggerFetch(),
            err => this.logger.error("ProjectService failed to refresh token")
        );
    }

    /**
     * Returns a stream of the current Project[]
     */
    getProjects(): Observable<Project[]> {
        return this._projectsSubject.asObservable();
    }

    /**
     * Returns the default project or null if the default project is not found.
     */
    getDefaultProject(): Project {
        let returnVal: Project = null;
        let projects = this._projectsSubject.getValue();
        let matches = projects.filter((proj) => proj.name == this._defaultProjectName);
        if (matches.length >= 1) {
            returnVal = matches[0];
        }
        return returnVal;
    }

    /**
     * Returns the default project or null if the default project is not found.
     *    TODO: Revisit this solution while doing KNOW-410
     *    See https://opensource.ncsa.illinois.edu/jira/browse/KNOW-410
     */
    getDefaultProjectAsync(): Observable<Project> {
        return this.getProjects().map(projects => {
            let returnVal: Project = null;
            let matches = projects.filter((proj) => proj.name == this._defaultProjectName);
            if (matches.length >= 1) {
                returnVal = matches[0];
            }
            return returnVal;
        }).share();
    }

    /**
     * Given a project id, returns the project object from the list already in
     * memory.
     */
    getProject(id: number): Project {
        let returnVal: Project = null;
        let projects = this._projectsSubject.getValue();
        let matches = projects.filter((proj) => proj._id == id);
        if (matches.length >= 1) {
            returnVal = matches[0];
        }
        return returnVal;
    }

    /**
     * Fetches the current projects from the server. Ensures the default project
     * exists, creating it if necessary.
     *
     * Why not make getDefaultProject() responsible for lazily creating the
     * default project? If we did it that way, then only callers of
     * getDefaultProject() could trigger the creation. The problem is there are
     * many other clients of this service that don't have any use for
     * getDefaultProject() but do need the complete list of projects, and that
     * list should always include the default.
     */
    triggerFetch() {
        // fetch the current projects from the server
        var requestStream = this.authHttp
            .get(this._projectUrl)
            .map(res => {
                let projectData: any[] = res.json()._items;
                return projectData.map((projectDatum: any) => new Project(
                    projectDatum._id,
                    projectDatum.name));
            });
        // add the array from the server to the stream of current projects
        requestStream.subscribe(
            pArr => {
                this._projectsSubject.next(pArr);
            },
            err => {
                this.logger.error("Failed fetching project data");
            });
    }

    /**
     * send a POST requst to api to create a new project
     * name: the project name
     */
    createProject(name: string): void {
        var headers = new Headers();
        headers.append('Content-Type', 'application/json');
        // post the new project to the server
		var url = this._projectUrl + '?reply=whole';
        var requestStream = this.authHttp
            .post(url, JSON.stringify({name}), {headers: headers})
            .map(res => {
                let projectDatum: any = res.json();
                return new Project(
                    projectDatum._id,
                    projectDatum.name);
            });
        // add the new project to the current Project[] and publish the updated
        // Project[] to the _projectsSubject stream
        requestStream.subscribe(
            proj => {
                var currentProjects = this._projectsSubject.getValue();
                currentProjects.push(proj);
                this._projectsSubject.next(currentProjects);
            },
            err => {
                this.logger.error("Failed creating project: " + name);
            }
        );
    }
}
