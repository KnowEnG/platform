import traceback

from nest_py.core.api_clients.http_client import NestHttpRequest
from nest_py.core.data_types.nest_id import NestId

class CrudApiClient(object):
    """
    Abstraction for Creating, Reading, Updating, and Deleting entries through
    a Rest Api. Assumes the semantics of NestCrudCollectionEndpoint and
    NestCrudEntryEndpoint for doing operations at the collection level
    (create new entry, query the collection) and entry level (read,
    update, delete a particular entry).

    The basic pattern: if a call fails for any reason, logs a detailed
    message and returns None.

    If Create/Update commands succeed, normally returns the
    object with it's nest_id set.

    If Delete command succeeds, returns the nest_id of what was deleted.

    If a Read command succeeds, returns the data payload parsed into
    dicts and lists, then to the actual data-type object by the abstract
    method transcoder.jdata_to_object()
    """

    def __init__(self, http_client, relative_url, json_transcoder):
        """
        http_client(NestHttpClient) configured to point to a server:port
            running a Nest Eve Server
        relative_url(String) relative url of a an endpoint
        json_transcoder(ApiJsonTranscoder) converts the data type of
            entries to/from jdata primitives

        e.g. for http://localhost/api/v1/foo/bar

        the http client is configured for server='localhost', port=80
        the relative_url is 'foo/bar',
        """
        self.http_client = http_client
        self.relative_url = relative_url
        self.transcoder = json_transcoder
        return

    def get_http_client(self):
        return self.http_client

    def get_collection_name(self):
        #TODO: relative url wasn't meant to carry the name of the collection,
        #but need it here for compatibility with crud_db_client. In practice
        #this currently is the same thing (collection_name is used as the
        #relative url everywhere)
        return self.relative_url

    def response_of_create_entry(self, dto, timeout_secs=60.0, verbose_errors=True, num_tries=3, reply='id'):
        """
        Performs a POST call to this client's endpoint and returns
        the full response object.
        Prefer to use create_entry() if you don't need fine grained
        error handling.
        reply (str): one of 'id', 'count', or 'whole' for whether you
            want the response to contain just the created id, a count
            of how many succesfully created, or the whole object
        """
        jdata = self.transcoder.object_to_jdata(dto)
        #files_dict = self._dto_to_files_dict(dto)
        request = NestHttpRequest(\
            self.relative_url,
            op="POST",
            http_params={'reply': reply},
            data=jdata,
            num_tries=num_tries,
            require_json=True,
            timeout_secs=timeout_secs)

        response = self.http_client.perform_request(request, verbose_errors=verbose_errors)
        return response

    def create_entry(self, dto, timeout_secs=60.0):
        """
        same as response_of_create_entry, but returns the
        eve_attributes on success and None on any failure
        """
        response = self.response_of_create_entry(dto, timeout_secs=timeout_secs)
        if response.did_succeed():
            try:
                jdata = response.get_data_payload_as_jdata()
                nest_id = NestId(jdata['created_id'])
                dto.set_nest_id(nest_id)
            except Exception as e:
                traceback.print_exc()
                log("create_entry error transforming json data to object")
                log("Exception: " + str(e))
                dto = None
        else:
            dto = None
        return dto

    def response_of_bulk_create_entries(self, dto_lst, timeout_secs=60.0, reply='id'):
        """
        Note that this has no batch_size, just uploads all in one call,
        while bulk_create_entries() lets you set a batch_size

        reply (str): one of 'id', 'count', or 'whole' for whether you
            want the response to contain just the created id, a count
            of how many succesfully created, or the whole object
        """
        jdata = list()
        for dto in dto_lst:
            jdata.append(self.transcoder.object_to_jdata(dto))

        params = {'reply': reply}
        request = NestHttpRequest(\
            self.relative_url,
            op="POST",
            http_params=params,
            data=jdata,
            files=None,
            require_json=True,
            timeout_secs=timeout_secs)

        response = self.http_client.perform_request(request)
        return response

    def bulk_create_entries(self, dto_lst, batch_size=100, timeout_secs=60.0):
        """
        """
        if len(dto_lst) == 0:
            return list()

        acc_created = list()
        batches = self._split_to_batches(dto_lst, batch_size)
        for batch in batches:
            response = self.response_of_bulk_create_entries(
                batch, timeout_secs=timeout_secs, reply='id')
            if response.did_succeed():
                try:
                    #this jdata should be a list of ints, which are
                    #nest_ids of the entries just created in the database
                    jdata = response.get_data_payload_as_jdata()
                    num_created = jdata['num_created']
                    nest_ids = jdata['created_ids']
                    assert(num_created == len(batch))
                    assert(num_created == len(nest_ids))
                    for nid, dto in zip(nest_ids, batch):
                        nest_id = NestId(nid)
                        dto.set_nest_id(nest_id)
                        acc_created.append(dto)
                except Exception as e:
                    traceback.print_exc()
                    log("bulk_create_entries() error transforming json data to NestId")
                    log("Exception: " + str(e))
                    accs_created = None
                    break
            else:
                acc_created = None
        return acc_created

    def bulk_create_entries_async(self, dto_lst, batch_size=100, timeout_secs=60.0):
        """
        """
        if len(dto_lst) == 0:
            return list()

        batches = self._split_to_batches(dto_lst, batch_size)
        num_created = 0
        for batch in batches:
            response = self.response_of_bulk_create_entries(
                batch, timeout_secs=timeout_secs, reply='count')
            if response.did_succeed():
                try:
                    #this jdata should be a list of ints, which are
                    #nest_ids of the entries just created in the database
                    jdata = response.get_data_payload_as_jdata()
                    num_created += jdata['num_created']
                except Exception as e:
                    traceback.print_exc()
                    log("bulk_create_entries() error transforming json data to NestId")
                    log("Exception: " + str(e))
                    num_created = None
                    break
            else:
                num_created = None
        return num_created


    def response_of_read_entry(self, nest_id, num_tries=3):
        """
        Performs a GET call to this client's endpoint and returns
        the full response object.

        Prefer to use read_entry() if you don't need fine grained
        error handling.

        nest_id(NestId): NestObject 'id' of the entry we want to fetch
        """
        params = dict()
        id_str = str(nest_id.get_value())
        relative_url = self.relative_url + '/' + id_str
        request = NestHttpRequest(\
            relative_url,
            op="GET",
            http_params=params,
            num_tries=num_tries,
            require_json=True)

        response = self.http_client.perform_request(request)
        return response

    def read_entry(self, nest_id, num_tries=3):
        """
        see response_of_read_entry()

        nest_id(NestId): nest_id of the entry we want to fetch
        """
        response = self.response_of_read_entry(nest_id, num_tries=num_tries)
        if response.did_succeed():
            try:
                jdata = response.get_data_payload_as_jdata()
                nid = jdata['_id']
                nest_id = NestId(nid)
                dto = self.transcoder.jdata_to_object(jdata)
                dto.set_nest_id(nest_id)
            except Exception as e:
                traceback.print_exc()
                log("create_entry error transforming json data to object")
                log("Exception: " + str(e))
                dto = None
        else:
            dto = None
        return dto

    def response_of_simple_filter_query(self, filter_params, max_results=None, page=None, fields=None, sort_fields=None):
        """
        does a GET for all entries that match the filter_params

        filter_params is a dictionary of kvps.
        all EveEntries at the endpoint are expected to have
        a value for each key being matched (but only some
        will match the filter value)

        So if all the entries look like this:
            { x: 'xi', y: 'yj', z:'zk'}

        then, simple_query_filter({x:'x1', y:'y1'})
        would match all entries where x=x1 and y=y1.
        """
        relative_url = self.relative_url
        final_params = dict(filter_params)
        if not max_results is None:
            final_params['max_results'] = max_results
        if not page is None:
            final_params['page'] = page
        if not fields is None:
            final_params['fields'] = ','.join(fields)
        if not sort_fields is None:
            final_params['sort'] = ','.join(sort_fields)

        request = NestHttpRequest(\
            relative_url,
            op="GET",
            http_params=final_params,
            require_json=True)

        response = self.http_client.perform_request(request)
        return response

    def simple_filter_query(self, filter_params, max_results=None, page=None, fields=None, sort_fields=None):
        """
        max_results and page (ints) control pagination. They are only included
        in the request params if they are not None
        """
        response = self.response_of_simple_filter_query(\
            filter_params,  max_results=max_results, page=page, fields=fields,
            sort_fields=sort_fields)
        if response.did_succeed():
            try:
                jdata = response.get_data_payload_as_jdata()
                dto_lst = list()
                for jdata_entry in jdata['_items']:
                    if fields is None:
                        dto = self.transcoder.jdata_to_object(jdata_entry)
                        nid = NestId(jdata_entry['_id'])
                        dto.set_nest_id(nid)
                    else:
                        dto = jdata_entry
                    dto_lst.append(dto)
            except Exception as e:
                traceback.print_exc()
                log("create_entry error transforming json data to object")
                log("Exception: " + str(e))
                dto_lst = None
        else:
            dto_lst = None
        return dto_lst

    def response_of_update_entry(self, nest_id, dto, timeout_secs=60.0):
        """
        Performs a PATCH call to this client's endpoint and returns
        the full response object.

        Also note that as of December 2015, we expect most endpoints won't
        allow updates; to check/configure, look for 'PATCH' among the
        item_methods in the endpoint's portion of the Eve domain.

        Prefer to use update_entry() if you don't need fine grained
        error handling.

        nest_id(NestId): lookup key of the entry we want to alter
        dto(object): an object of the type this crud_client understands
            for abstract method and transcoder.object_to_jdata
        timeout_secs(float): time to wait for HTTP response
        """
        params = dict()

        headers = dict()
        jdata = self.transcoder.object_to_jdata(dto)
        nid = nest_id.get_value()
        jdata['_id'] = nid
        relative_url = self.relative_url + '/' + str(nid)
        request = NestHttpRequest(\
            relative_url,
            op="PATCH",
            http_params=params,
            headers=headers,
            data=jdata,
            require_json=True,
            timeout_secs=timeout_secs)

        response = self.http_client.perform_request(request)
        return response

    def update_entry(self, nest_id, dto, timeout_secs=60.0):
        """
        same as response_of_update_entry, but returns the
        eve_attributes on success and None on any failure
        """
        response = self.response_of_update_entry(\
            nest_id, dto, timeout_secs)
        if response.did_succeed():
            try:
                jdata = response.get_data_payload_as_jdata()
                nid = NestId(jdata['updated_id'])
                #this should be replacing the NestId with an identical one
                dto.set_nest_id(nid)
            except Exception as e:
                traceback.print_exc()
                log("update_entry error transforming json data to object")
                log("Exception: " + str(e))
                dto = None
        else:
            dto = None
        return dto

    def response_of_delete_entry(self, nest_id):
        """
        Performs a DELETE call to this client's endpoint and returns
        the full response object.
        Prefer to use delete_entry() if you don't need fine grained
        error handling.

        A good response has code 204 and jdata that is just
            {'deleted_id':<nest_id>}

        nest_id(NestId): _id of the entry to delete on the server
        """
        params = dict()
        headers = dict()
        id_str = str(nest_id.get_value())
        relative_url = self.relative_url + '/' + id_str
        request = NestHttpRequest(\
            relative_url,
            op="DELETE",
            http_params=params,
            headers=headers,
            require_json=True)

        response = self.http_client.perform_request(request)
        return response

    def delete_entry(self, nest_id):
        """
        returns the input nest_id if it is succesfully deleted,
        None on failure
        """
        deleted_id = None
        response = self.response_of_delete_entry(nest_id)
        if response.did_succeed():
            try:
                jdata = response.get_data_payload_as_jdata()
                log('delete response data: ' + str(jdata))
                deleted_id = NestId(jdata['deleted_id'])
                assert(nest_id == deleted_id)
            except Exception as e:
                traceback.print_exc()
                log("update_entry error transforming json data to object")
                log("Exception: " + str(e))
                deleted_id = None

        return deleted_id

    def response_of_delete_all_entries(self):
        """
        Performs a DELETE call to this client's collection endpoint
        and returns the full response object.

        This is a dangerous method so there is not a corresponding
        convenience method delete_all_entries()

        A good response has code 204 and jdata that is just
            {'num_deleted':count}

        nest_id(NestId): _id of the entry to delete on the server
        """
        params = dict()
        headers = dict()
        collections_url = self.relative_url
        request = NestHttpRequest(\
            collections_url,
            op="DELETE",
            http_params=params,
            headers=headers,
            require_json=True)

        response = self.http_client.perform_request(request)
        return response


#    def _dto_to_files_dict(self, dto):
#        """
#        extract file information, if present, from dto
#        """
#        files_dict = None
#        if hasattr(self, 'object_to_files_dict') and \
#            callable(getattr(self, 'object_to_files_dict')):
#            #pylint: disable=no-member
#            files_dict = self.object_to_files_dict(dto)
#            #pylint: enable=no-member
#        return files_dict
#
    def _split_to_batches(self, dto_lst, batch_size):
        """
        splits a list of dtos into batches and also does
        the transform to jdata (with error checks)
        returns a list of lists of jdata
        """
        entries_idx = 0
        num_entries = len(dto_lst)
        batches = list()
        while entries_idx < num_entries:
            current_batch = list()
            batch_idx = 0
            while (entries_idx < num_entries) and (batch_idx < batch_size):
                current_batch.append(dto_lst[entries_idx])
                batch_idx += 1
                entries_idx += 1
            batches.append(current_batch)
        #log('batches: ' + str(batches))
        return batches


def log(msg):
    print msg
