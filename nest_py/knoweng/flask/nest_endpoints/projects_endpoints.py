"""This module defines a set of hooks for the project endpoint.
"""
import json
import os
import shutil
import flask

import nest_py.knoweng.data_types.projects as projects
from nest_py.knoweng.data_types.projects import ProjectDTO
from nest_py.core.flask.nest_endpoints.nest_endpoint_set import NestEndpointSet
from nest_py.core.flask.nest_endpoints.crud_endpoints import NestCrudCollectionEndpoint
from nest_py.core.flask.nest_endpoints.crud_endpoints import NestCrudEntryEndpoint
from nest_py.core.data_types.nest_id import NestId

def get_endpoint_set(project_db_client, authenticator):

    rel_url = projects.COLLECTION_NAME
    api_transcoder = projects.generate_schema()        

    collection_ep = ProjectCollectionEndpoint(rel_url, 
        project_db_client, api_transcoder, authenticator)
    entry_ep = ProjectEntryEndpoint(rel_url, 
        project_db_client, api_transcoder, authenticator) 
    eps = NestEndpointSet()
    eps.add_endpoint(collection_ep)
    eps.add_endpoint(entry_ep)
    return eps

class ProjectCollectionEndpoint(NestCrudCollectionEndpoint):
    """Defines hooks for the project endpoint."""

    def __init__(self, rel_url, crud_db_client, api_transcoder,
        authenticator):
        super(ProjectCollectionEndpoint, self).__init__(
            rel_url, crud_db_client, api_transcoder, authenticator)

        config = flask.current_app.config
        self.userfiles_dir = config['USERFILES_DIR']
        return

    def do_POST(self, request, requesting_user):
        """Handle new project by creating a directory under
        userfiles_dir.

        Args:
            request (flask.request): The request object.
        """
        if isinstance(request.get_json(), list):
            raise Exception("projects endpoint doesn't support bulk uploads")
        if request.args['reply'] == 'count':
            raise Exception("projects endpoint doesn't support 'reply=count'")
        response = super(ProjectCollectionEndpoint, self).do_POST(request, requesting_user)
        fields = json.loads(response.response[0])
        print(str(fields))
        if 'created_id' in fields:
            nid = NestId(int(fields['created_id']))
        if '_id' in fields:
            nid = NestId(int(fields['_id']))

        project_dir = projects.project_dirpath(self.userfiles_dir, nid)
        os.mkdir(project_dir)
        return response

    def do_DELETE(self, request, requesting_user):
        """
        When all entries in the collection are deleted, also delete
        the files for all projects
        Note that this will delete only the projects the user
            can access, so use a superuser to delete everything
        """
        try:
            all_tles = self.crud_client.simple_filter_query({}, 
                user=requesting_user)
            num_deleted = 0
            for tle in all_tles:
                project = ProjectDTO.from_tablelike_entry(tle)
                nid = project.get_nest_id()
                nm = project.name
                print('Deleting project: ' + nm + ', ' + nid.to_slug())
                project_dir = project.get_dirpath(self.userfiles_dir)
                shutil.rmtree(project_dir)
                deleted_nid = self.crud_client.delete_entry(nid, 
                    user=requesting_user)
                if deleted_nid is not None:
                    num_deleted += 1
            jdata = dict()
            jdata['num_deleted'] = num_deleted
            resp = self._make_success_json_response(jdata)
        except Exception as e:
            resp = self._make_error_response('delete all failed: ' +
                str(e))
        return resp

class ProjectEntryEndpoint(NestCrudEntryEndpoint):

    def __init__(self, rel_url, crud_db_client, api_transcoder,
        authenticator):
        super(ProjectEntryEndpoint, self).__init__(
            rel_url, crud_db_client, api_transcoder, authenticator)

        config = flask.current_app.config
        self.userfiles_dir = config['USERFILES_DIR']
        return

    def do_DELETE(self, request, requesting_user, nid_int):
        """Delete project from the disk.

        Args:
            request (flask.request): The request object.
        """
        response = super(ProjectEntryEndpoint, self).do_DELETE(
            request, requesting_user, nid_int)
        if response.status_code == 200:#TODO: 204 would be more precise
            # delete single project
            fields = json.loads(response.response[0])
            nid = NestId(int(fields['deleted_id']))
            project_dir = projects.project_dirpath(self.userfiles_dir, nid)
            shutil.rmtree(project_dir)
        return response

