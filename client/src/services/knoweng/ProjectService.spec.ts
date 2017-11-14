// src/services/knoweng/ProjectService.spec.ts
import { inject, async, TestBed, fakeAsync, tick } from '@angular/core/testing';
import { Injectable, ReflectiveInjector } from '@angular/core';
import { MockBackend, MockConnection } from '@angular/http/testing';

import { Http, Headers, BaseRequestOptions, Response, RequestOptions, ConnectionBackend } from '@angular/http';
import { AuthHttp,AuthConfig } from 'angular2-jwt';
import { Observable } from 'rxjs/Observable';
import { BehaviorSubject } from 'rxjs/BehaviorSubject';

import { ProjectService } from './ProjectService';
import { Project } from '../../models/knoweng/Project'

describe('ProjectService', () => {
  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [  ],
      providers: [
        ProjectService,
        {
          provide: Http,
          useFactory: (backendInstance: MockBackend, defaultOptions: BaseRequestOptions) => {
            return new Http(backendInstance, defaultOptions);
          },
          deps: [MockBackend, BaseRequestOptions]
        },
        {
          provide: AuthHttp,
          useExisting: Http,
          deps: [Http]
        },
        MockBackend,
        BaseRequestOptions
      ]
    });
  });
  
  describe('getProjects: ', () => {
    it('Parsing projects from api response', () => {
      inject([ProjectService, MockBackend], fakeAsync((service: any, backend: any) => {
        var projects : Project[];
      
        // TODO: Abstract this elegantly somehow?
        backend.connections.subscribe((connection: any) => { 
          this.lastConnection = connection;
          
          connection.mockRespond(new Response(<any>{
            body: `
            {
              "_items": [{"_id": "56c156b18870e300012950ea", "name": "xx-test"}], "_meta": {"total": 1, "page": 1, "max_results": 100}
            }
            `
          }));
        });

        service.getProjects().subscribe((projects: Project[]) => this.projects = projects,
                                (error: any) => alert(`Server error. Try again later`));
        tick();
      
        // Assert that target connection did not fail in some eg
        // TODO: Abstract this elegantly somehow?
        expect(this.lastConnection).toBeDefined('no http service connection at all?');
        expect(this.lastConnection.request.url).toMatch(/api\/v2\/projects/, 'url invalid');

        // Assert that our expected mock dataset is correct
        expect(projects.length).toEqual(1);
        
        // Assert that our mock data item contains the expected values
        let project = projects[0];
        expect(project._id).toEqual('56c156b18870e300012950ea');
        expect(project.name).toEqual('xx-test');
      }));
    });
  });
});
