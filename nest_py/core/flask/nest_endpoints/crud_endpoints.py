import traceback
import flask
from nest_py.core.flask.nest_endpoints.nest_endpoint import NestEndpoint
from nest_py.core.data_types.nest_id import NestId

class NestCrudEntryEndpoint(NestEndpoint):
    """
    Supports Read, Update, Delete of a single entry that is
    specified by an id, at endpoint "api/v2/<relative_url>/<:id>"
    using GET, PATCH and DELETE
    """

    def __init__(self, relative_url, crud_db_client, json_transcoder, authenticator):
        """
        """
        self.crud_client = crud_db_client
        self.transcoder = json_transcoder
        super(NestCrudEntryEndpoint, self).__init__(relative_url, authenticator)
        return

    def get_flask_rule(self):
        rel_url = self.get_relative_url()
        rule = rel_url +'/<int:nid_int>'
        return rule
    
    def get_flask_endpoint(self):
        rel_url = self.get_relative_url()
        flask_ep = rel_url + '/entry'
        return flask_ep

    def do_GET(self, request, requesting_user, nid_int):
        nid = NestId(nid_int)
        dto = self.crud_client.read_entry(nid, user=requesting_user)
        if dto is None:
            resp = flask.make_response('unknown id for type ' +
                self.get_flask_endpoint(), 404)
        else:
            jdata = self.transcoder.object_to_jdata(dto)
            resp = self._make_success_json_response(jdata)
        return resp

    def do_PATCH(self, request, requesting_user, nid_int):
        nest_id = NestId(nid_int)
        jdata = request.get_json()
        dto = self.transcoder.jdata_to_object(jdata)
        dto.set_nest_id(nest_id)
        updated_dto = self.crud_client.update_entry(dto, user=requesting_user)
        if updated_dto is None:
            resp = self._make_error_response('Failed to update in DB')
        else:
            resp_jdata = self.format_update_single_jdata(request, updated_dto)
            resp = self._make_success_json_response(resp_jdata)
        return resp

    def format_update_single_jdata(self, request, created_dto):
        """
        given a dto that is already 'created' in the db (has an _id),
        prepare the json payload based on the user requested 
        reply_format.
	
        FIXME: cut and paste from NestCrudCollectionEndpoint
        """
        reply_format = _deduce_reply_format(request)
        if reply_format == 'id':
            nid = created_dto.get_nest_id().get_value()
            resp_jdata = dict()
            resp_jdata['updated_id'] = nid 
        elif reply_format == 'whole':
            resp_jdata = self.transcoder.object_to_jdata(created_dto)
        elif reply_format == 'count':
            resp_jdata = {'num_updated': 1}
        else:
            raise Exception('invalid reply param value')
        return resp_jdata


    def do_DELETE(self, request, requesting_user, nid_int):
        nid = NestId(nid_int)
        deleted_nid = self.crud_client.delete_entry(nid, user=requesting_user)
        if deleted_nid is None:
            resp = self._make_error_response('DB delete failed')
        else:
            jdata = dict()
            jdata['deleted_id'] = deleted_nid.get_value()
            #FIXME should return 204
            resp = self._make_success_json_response(jdata)
        return resp

class NestCrudCollectionEndpoint(NestEndpoint):
    """
    Support Create (New Entry), Read (by Query) of entries at
    endpoints like "api/v2/<relative_url>" 

    Style of endpoint where a data type (DTO) is written to database
    and read back (and other CRUD operations). Requires a
    working CrudDBClient to write to the database and
    a way of translating the DTO
    """

    def __init__(self, relative_url, crud_db_client, json_transcoder, authenticator):
        """
        """
        self.crud_client = crud_db_client
        self.transcoder = json_transcoder
        super(NestCrudCollectionEndpoint, self).__init__(relative_url, authenticator)
        return

    def get_flask_rule(self):
        rel_url = self.get_relative_url()
        rule = rel_url 
        return rule
    
    def get_flask_endpoint(self):
        rel_url = self.get_relative_url()
        flask_ep = rel_url + '/collection'
        return flask_ep

    def do_GET(self, request, requesting_user):
        #(max_results, page) = self._extract_pagination_params(request)

        #separate the pagination params from the filter params
        #note that every value in request.args dict is a list
        filter_query = dict(request.args)
        log('filter_query: ' + str(filter_query))
        if 'max_results' in filter_query:
            max_results = int(filter_query.pop('max_results')[0])
        else:
            max_results = None
        if 'page' in filter_query:
            page = int(filter_query.pop('page')[0])
        else:
            page = None
        if 'fields' in filter_query:
            raw_fields = filter_query.pop('fields')
            fields = self._parse_fields_comma_query(raw_fields)
            print('crud_endpoints: final fields:' + str(fields))
        else:
            fields = None
        if 'sort' in filter_query:
            raw_sort = filter_query.pop('sort')
            sort_fields = self._parse_fields_comma_query(raw_sort)
            print('crud_endpoints: final sort_fields:' + str(sort_fields))
        else:
            sort_fields = None

        for k in filter_query:
            filter_query[k] = self._parse_comma_query(filter_query[k])
            if k == '_id':
                filter_query['id'] = filter_query.pop('_id')

        query_res = self.crud_client.paged_filter_query(filter_query,
            user=requesting_user, results_per_page=max_results, 
            page_num=page, fields=fields, sort_fields=sort_fields)
        jdata_items = list()
        for dto in query_res['items']:
            if fields is None:
                jd = self.transcoder.object_to_jdata(dto)
            else:
                jd = dto #the db client will have just returned a dict
                #the API Transcoder interface requires the returned json
                #to have an '_id' field, not an 'id' field as postgres
                #uses. We have bypassed the transcoder here so we
                #must enforce the correction here
                if 'id' in jd:
                    jd['_id'] = jd.pop('id')
            jdata_items.append(jd)
        jdata_meta = dict()
        jdata_meta['page'] = query_res['page']
        jdata_meta['total_available_items'] = query_res['total_available']
        jdata_meta['num_items'] = query_res['num_items']
        jdata_meta['last_page'] = query_res['last_page']
        jdata = dict()
        jdata['_items'] = jdata_items
        jdata['_meta'] = jdata_meta
        resp = self._make_success_json_response(jdata)
        return resp

    def _parse_comma_query(self, list_of_strings):
        """
        list_of_strings: from flask args, might be already parsed
        into a list of values if the url was like:
            blah.com?key=val1&key=val2&key=val3
        but will be a single entry of ['val1,val2,val3'] if 
        the url was:
            blah.com?key=val1,val2,val3

        this figures it all out and returns ['val1', 'val2', 'val3']
        """
        parsed_vals = list()
        for raw_val in list_of_strings:
            for val in raw_val.split(','):
                val2 = val.strip()
                parsed_vals.append(val2)
        return parsed_vals

    def _parse_fields_comma_query(self, list_of_fields):
        """
        same as _parse_comma_query, but expect the values to
        be valid fields for the data_type. Does the conversion
        of '_id'->'id' that the database layer requires. (Retains
        field order)
        """
        parsed_fields = self._parse_comma_query(list_of_fields)
        for i in range(len(parsed_fields)):
            if parsed_fields[i] == '_id':
                parsed_fields[i] = 'id'
        return parsed_fields


    def do_POST(self, request, requesting_user):
        """
        'reply' arg can be:
            ?reply=id  : 'created_id': <id> or list of <id>
            ?reply=count: num_create: <count>
            ?reply=whole: {_id: <id>, ...+  all other fields of the entry}
        """
        jdata = request.get_json()
        #print('do_POST user: ' + str(requesting_user.get_username()))
        if isinstance(jdata, list):
            resp = self._create_batch_entries(request, requesting_user)
        else:
        #TODO: maybe the 'create_single' path should just follow the batch
        #path. Clients getting a list of size one isn't a big deal, but there
        #is a lot of code here to avoid it.

            resp = self._create_single_entry(request, requesting_user)
        return resp

    def _create_single_entry(self, request, requesting_user):
        request_jdata = request.get_json()
        dto = self.transcoder.jdata_to_object(request_jdata)
        dto = self.crud_client.create_entry(dto, user=requesting_user)
        if dto is None:
            resp = self._make_error_response('Write to DB failed')
        else:
            resp_jdata = self.format_create_single_jdata(request, dto)
            resp = self._make_success_json_response(resp_jdata)
        return resp

    def format_create_single_jdata(self, request, created_dto):
        """
        given a dto that is already 'created' in the db (has an _id),
        prepare the json payload based on the user requested 
        reply_format.
        """
        reply_format = _deduce_reply_format(request)
        if reply_format == 'id':
            nid = created_dto.get_nest_id().get_value()
            resp_jdata = dict()
            resp_jdata['created_id'] = nid 
        elif reply_format == 'whole':
            resp_jdata = self.transcoder.object_to_jdata(created_dto)
        elif reply_format == 'count':
            resp_jdata = {'num_created': 1}
        else:
            raise Exception('invalid reply param value')
        return resp_jdata

    def _create_batch_entries(self, request, requesting_user):
        #print('create_batch_entry user: ' + str(requesting_user.get_username()))

        reply_format = _deduce_reply_format(request)
        request_jdata = request.get_json()

        dtos = list()
        for obj_jd in request_jdata:
            #print('jd_to_obj for jd: ' + str(obj_jd))
            dtos.append(self.transcoder.jdata_to_object(obj_jd))

        db_batch_size = len(dtos)
        resp_jdata = dict()
        if reply_format == 'id':
            dtos = self.crud_client.bulk_create_entries(dtos, 
                user=requesting_user, batch_size=db_batch_size)
            nids = list()
            for dto in dtos:
                nid = dto.get_nest_id().get_value()
                nids.append(nid)
            resp_jdata['created_ids'] = nids
            resp_jdata['num_created'] = len(nids)
        elif reply_format == 'count':
            num_created = self.crud_client.bulk_create_entries_async(
                dtos, user=requesting_user, batch_size=db_batch_size)
            resp_jdata['num_created'] = num_created
        elif reply_format == 'whole':
            dtos = self.crud_client.bulk_create_entries(dtos, 
                user=requesting_user, batch_size=db_batch_size)
            createds = list()
            for dto in dtos:
                obj_jdata = self.transcoder.object_to_jdata(dto)
                createds.append(obj_jdata)
            resp_jdata['created_entries'] = createds
            resp_jdata['num_created'] = len(createds)
        resp = self._make_success_json_response(resp_jdata)
        return resp
        

    def do_DELETE(self, request, requesting_user):
        num_deleted = None
        try:
            num_deleted = self.crud_client.delete_all_entries(user=requesting_user)
        except Exception:
            traceback.print_exc()
        if num_deleted is None:
            resp = self._make_error_response('DB delete failed')
        else:
            jdata = dict()
            jdata['num_deleted'] = num_deleted
            resp = self._make_success_json_response(jdata)
        return resp


    def _extract_pagination_params(self, request):
        http_args = request.args
        if http_args.has_key('max_results'):
            max_results = int(http_args['max_results'])
        else:
            max_results = None
        if http_args.has_key('page'):
            page = int(http_args['page'])
        else:
            page = None
        return (max_results, page)
     
def _deduce_reply_format(request):
    if 'reply' in request.args:
        reply_format = request.args['reply']
    else:
        reply_format = 'id'
    assert(reply_format in ['id', 'count', 'whole'])
    return reply_format
   
def log(msg):
    print(msg)
