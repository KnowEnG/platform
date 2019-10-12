from nest_py.hello_world.data_types.simplest_dto import SimplestDTO
from nest_py.hello_world.data_types.simplest_dto import SimplestDTOTranscoder
import nest_py.hello_world.data_types.simplest_dto as simplest_dto
from nest_py.core.api_clients.api_client_maker import ApiClientMaker
from nest_py.core.api_clients.crud_api_client import CrudApiClient
import nest_py.core.api_clients.smoke_scripts as smoke_scripts

class SimplestDTOApiClientMaker(ApiClientMaker):

    def __init__(self):
        name = simplest_dto.COLLECTION_NAME
        super(SimplestDTOApiClientMaker, self).__init__(name)
        return

    def get_crud_client(self, http_client):
        api_transcoder = SimplestDTOTranscoder()
        ac = CrudApiClient(http_client, self.name, api_transcoder)
        return ac

    def run_smoke_scripts(self, http_client, result_acc):
        
        crud_client = self.get_crud_client(http_client)
        smoke_auth(crud_client, result_acc)
        smoke_simplest_dto_crud(crud_client, result_acc)
        smoke_simplest_dto_pagination(crud_client, result_acc)
        smoke_simplest_dto_bulk_writes(crud_client, result_acc)
        smoke_simplest_dto_fields_projection(crud_client, result_acc)
        smoke_simplest_dto_sort(crud_client, result_acc)
        smoke_simplest_dto_create_reply_param(crud_client, result_acc)
        return

def smoke_auth(crud_client, result_acc):
    """
    tries to do a POST with and without the token. passes if it fails
    with no token and succeeds with the token.
    """
    result_acc.add_report_line('BEGIN smoke_auth()')
    http_client = crud_client.http_client
    http_client.logout()
    example_entry = SimplestDTO(message='hi')
    no_tok_response = crud_client.response_of_create_entry(
        example_entry, verbose_errors=False, num_tries=1)
    if no_tok_response.did_succeed():
        result_acc.add_report_line("no auth upload succeeded when it " +
            "should have failed")
        result_acc.set_success(False)
    else:
        if not no_tok_response.get_http_code() == 401:
            result_acc.set_success(False)
            result_acc.add_report_line("no auth upload failed as it should, " + 
                "but the error code was not 401/unauthorized: " + 
                str(no_tok_response.get_http_code()))
            
 
    #log back in and try again, it should work
    smoke_scripts.login_client(http_client, result_acc)
    tok_response = crud_client.response_of_create_entry(example_entry)
    if not tok_response.did_succeed():
        result_acc.set_success(False)
        result_acc.add_report_line("auth upload failed with code: " + 
            str(tok_response.get_http_code()))
    result_acc.add_report_line('END smoke_auth()')
    return

def smoke_simplest_dto_crud(crud_client, result_acc):
    """
    http_client(BasicHttpClient)
    """
    result_acc.add_report_line('BEGIN smoke_simplest_dto_crud()')

    dto_0 = SimplestDTO(message='hello')
    dto_1 = crud_client.create_entry(dto_0)
    if dto_1 is None:
        result_acc.add_report_line("create_entry failed")
        result_acc.set_success(False)
        return
    else:
        nest_id = dto_1.get_nest_id()
        result_acc.add_report_line("created entry with id: " + str(nest_id))

    dto_2 = crud_client.read_entry(nest_id)
    result_acc.add_report_line('expected: ' + str(dto_0))
    result_acc.add_report_line('observed: ' + str(dto_2))
    if dto_2.message != dto_0.message:
        result_acc.set_success(False)

    dto_3 = SimplestDTO(id=nest_id.get_value(), message='hi')
    updated_dto_3 = crud_client.update_entry(nest_id, dto_3)
    if updated_dto_3 is None:
        result_acc.add_report_line("couldn't update what we just created")
        result_acc.set_success(False)
    else:
        result_acc.add_report_line("updated what we just created: " + \
            str(updated_dto_3.get_nest_id()))

        # get again
        dto_4 = crud_client.read_entry(nest_id)
        result_acc.add_report_line('expected: ' + str(updated_dto_3))
        result_acc.add_report_line('observed: ' + str(dto_4))
        if dto_3.message != dto_4.message:
            result_acc.set_success(False)

    deleted_id = crud_client.delete_entry(nest_id)
    if deleted_id is None:
        result_acc.add_report_line("couldn't delete what we just created")
        result_acc.set_success(False)
    else:
        result_acc.add_report_line("deleted what we just created: " + str(deleted_id))
    result_acc.add_report_line('END smoke_simplest_dto_crud()')
    return

def smoke_simplest_dto_pagination(crud_client, result_acc):
    """
    """
    result_acc.add_report_line('BEGIN smoke_simplest_dto_pagination()')

    data_set = list()
    for i in range(10):
        data_set.append(SimplestDTO(message='x'))

    for i in range(5):
        data_set.append(SimplestDTO(message='y'))

    saved_data = list()
    for dto in data_set:
        dto = crud_client.create_entry(dto)
        saved_data.append(dto)
        
    #test with explicit pagination getting page size of 6,
    #which should result in 6 then 4 results
    filter_xs = {'message':'x'}
    batch1 = crud_client.simple_filter_query(filter_xs, page=1, max_results=6)
    if batch1 is None:
        batch1 = list()
    if (not (len(batch1) == 6)):
        result_acc.set_success(False)
    result_acc.add_report_line('expected 6 results for message=x on page=1, got:' + 
            str(len(batch1)))

    batch2 = crud_client.simple_filter_query(filter_xs, page=2, max_results=6)
    if batch2 is None:
        batch2 = list()
    if not (len(batch2) == 4):
        result_acc.set_success(False)
    result_acc.add_report_line('expected 4 results for message=x on page=2, got:' + 
            str(len(batch2)))

    #max_results bigger than the num results we expect
    batch3 = crud_client.simple_filter_query(filter_xs, max_results=20)
    if batch3 is None:
        batch3 = list()
    if not (len(batch3) == 10):
        result_acc.set_success(False)
    result_acc.add_report_line('expected 10 results for message=x on page=1, got:' + 
            str(len(batch3)))

    #if a param is added twice, it should be treated as 'or', so this should return
    #all x's and all y's
    filter_xs_and_ys = {'message': ['x', 'y']}
    batch4 = crud_client.simple_filter_query(filter_xs_and_ys, max_results=20)
    if batch4 is None:
        batch4 = list()
    if not (len(batch4) == 15):
        result_acc.set_success(False)
    result_acc.add_report_line('expected 15 results for message=[x, y] on page=1, got:' + 
            str(len(batch4)))

    for dto in saved_data:
        crud_client.delete_entry(dto.get_nest_id())

    return 

def smoke_simplest_dto_fields_projection(crud_client, result_acc):
    """
    """
    result_acc.add_report_line('BEGIN smoke_simplest_dto_fields_projection()')
    resp = crud_client.response_of_delete_all_entries()
    if not resp.did_succeed():
        result_acc.add_report_line("delete all failed: " + resp.get_error_message())
    data_set = list()
    for i in range(10):
        data_set.append(SimplestDTO(message='f'))

    saved_data = crud_client.bulk_create_entries(data_set)

    if saved_data is None:
        result_acc.set_success(False)
        result_acc.add_report_line('bulk_create returned None')
    else:
        result_acc.add_report_line('bulk created ' + str(len(data_set)) +
            ' and got back ' + str(len(saved_data)))
        if (saved_data is None) or (not (len(data_set) == len(saved_data))):
            result_acc.set_success(False)
        
    filter_fs = {'message':'f'}
    fields = ['message']
    batch1 = crud_client.simple_filter_query(filter_fs, page=1, max_results=20, fields=fields)
    if batch1 is None:
        result_acc.set_success(False)
        result_acc.add_report_line('simple_filter_query returned None')
    else:
        result_acc.add_report_line('bulk created ' + str(len(data_set)) +
            ' js and simple_filter query gives back ' + str(len(batch1)))
        if not (len(data_set) == len(batch1)):
            result_acc.set_success(False)
        for json_item in batch1:
            for fn in ['message', '_id']: #the requested field and '_id' should be included
                if not fn in json_item:
                    result_acc.add_report_line('projected obj did not contain field: ' + fn)
                    result_acc.set_success(False)
            if len(json_item.keys()) != 2:
                    result_acc.add_report_line('too many fields in: ' + str(json_item))
                    result_acc.set_success(False)


def smoke_simplest_dto_bulk_writes(crud_client, result_acc):
    """
    """
    result_acc.add_report_line('BEGIN smoke_simplest_dto_bulk_writes()')
    resp = crud_client.response_of_delete_all_entries()
    if not resp.did_succeed():
        result_acc.add_report_line("delete all failed: " + resp.get_error_message())
    data_set = list()
    for i in range(10):
        data_set.append(SimplestDTO(message='j'))

    saved_data = crud_client.bulk_create_entries(data_set, batch_size=3)

    if saved_data is None:
        result_acc.set_success(False)
        result_acc.add_report_line('bulk_create returned None')
    else:
        result_acc.add_report_line('bulk created ' + str(len(data_set)) +
            ' and got back ' + str(len(saved_data)))
        if (saved_data is None) or (not (len(data_set) == len(saved_data))):
            result_acc.set_success(False)
        
    filter_js = {'message':'j'}
    batch1 = crud_client.simple_filter_query(filter_js, page=1, max_results=20)
    if batch1 is None:
        result_acc.set_success(False)
        result_acc.add_report_line('simple_filter_query returned None')
    else:
        result_acc.add_report_line('bulk created ' + str(len(data_set)) +
            ' js and simple_filter query gives back ' + str(len(batch1)))
        if not (len(data_set) == len(batch1)):
            result_acc.set_success(False)
     
    #batch size larger than data set size

    resp = crud_client.response_of_delete_all_entries()
    if not resp.did_succeed():
        result_acc.add_report_line("delete all failed: " + resp.get_error_message())
    data_set = list()
    for i in range(10):
        data_set.append(SimplestDTO(message='j'))
    saved2 = crud_client.bulk_create_entries(data_set, batch_size=20)
    if saved2 is None:
        result_acc.set_success(False)
        result_acc.add_report_line('bulk_create returned None')
    else:
        result_acc.add_report_line('bulk created ' + str(len(data_set)) +
            ' js with too large batch_size and got back ' + str(len(saved2)))
        if not (len(data_set) == len(saved2)):
            result_acc.set_success(False)

    data_k = list()
    for i in range(5):
        data_k.append(SimplestDTO(message='k'))

    num_created = crud_client.bulk_create_entries_async(data_k, batch_size=3)

    if num_created is None:
        result_acc.set_success(False)
        result_acc.add_report_line('bulk_create_async returned None')
    else:
        result_acc.add_report_line('bulk async created ' + str(len(data_k)) +
            ' ks and got back ' + str(num_created))
        if not (len(data_k) == num_created):
            result_acc.set_success(False)
    
    filter_ks = {'message':'k'}
    batch2 = crud_client.simple_filter_query(filter_ks, page=1, max_results=20)
    if batch2 is None:
        result_acc.set_success(False)
        result_acc.add_report_line('simple_filter_query after bulk_create_async returned None')
    else:
        result_acc.add_report_line('bulk async created ' + str(len(data_k)) +
            ' ks and query returned ' + str(len(batch2)))
        if not (len(data_k) == len(batch2)):
            result_acc.set_success(False)
    return 

def smoke_simplest_dto_sort(crud_client, result_acc):
    """
    """
    result_acc.add_report_line('BEGIN smoke_simplest_dto_sort()')
    resp = crud_client.response_of_delete_all_entries()
    if not resp.did_succeed():
        result_acc.add_report_line("delete all failed: " + resp.get_error_message())
    data_set = list()

    data_set.append(SimplestDTO(message='a1'))
    data_set.append(SimplestDTO(message='z8'))
    data_set.append(SimplestDTO(message='k2'))
    data_set.append(SimplestDTO(message='x4'))

    saved_data = crud_client.bulk_create_entries(data_set)

    if saved_data is None:
        result_acc.set_success(False)
        result_acc.add_report_line('bulk_create returned None')
    else:
        result_acc.add_report_line('bulk created ' + str(len(data_set)) +
            ' and got back ' + str(len(saved_data)))
        if (saved_data is None) or (not (len(data_set) == len(saved_data))):
            result_acc.set_success(False)
        
    sort_fields = ['message']
    batch1 = crud_client.simple_filter_query({}, page=1, max_results=20, sort_fields=sort_fields)
    if batch1 is None:
        result_acc.set_success(False)
        result_acc.add_report_line('simple_filter_query returned None')
    else:
        result_acc.add_report_line('bulk created ' + str(len(data_set)) +
            ' simple_filter query gives back ' + str(len(batch1)))
        if not (len(data_set) == len(batch1)):
            result_acc.set_success(False)
        for obs, exp in zip(batch1, ['a1', 'k2', 'x4', 'z8']):
            result_acc.add_report_line('sorted elem: ' + obs.message)
            if not obs.message == exp:
                result_acc.add_report_line('not sorted properly: exp: ' + 
                    exp + ', obs: ' + obs.message)
                result_acc.set_success(False)
    return

def smoke_simplest_dto_create_reply_param(crud_client, result_acc):
    """
    test the 'reply=xyz' param in the POST collection endpoint
    """
    result_acc.add_report_line('BEGIN smoke_simplest_dto_create_reply_param()')
    resp = crud_client.response_of_delete_all_entries()
    if not resp.did_succeed():
        result_acc.add_report_line("delete all failed: " + resp.get_error_message())

    dto1 = SimplestDTO(message='j')

    resp1_id = crud_client.response_of_create_entry(dto1, reply='id')
    if resp1_id.did_succeed():
        jdata = resp1_id.get_data_payload_as_jdata()
        if not 'created_id' in jdata:
            result_acc.add_report_line("didn't get back created_id in response")
            result_acc.set_success(False)
    else:
        result_acc.add_report_line("create_entry with reply='id' failed")
        result_acc.set_success(False)

    resp1_count = crud_client.response_of_create_entry(dto1, reply='count')
    if resp1_count.did_succeed():
        jdata = resp1_count.get_data_payload_as_jdata()
        if not 'num_created' in jdata and (jdata['num_created'] == 1):
            result_acc.add_report_line("didn't get back num_created = 1 in response")
            result_acc.set_success(False)
    else:
        result_acc.add_report_line("create_entry with reply='count' failed")
        result_acc.set_success(False)

 
    resp1_whole = crud_client.response_of_create_entry(dto1, reply='whole')
    if resp1_whole.did_succeed():
        jdata = resp1_whole.get_data_payload_as_jdata()
        if not (('message' in jdata) and (jdata['message'] == 'j')):
            result_acc.add_report_line("didn't get back whole entry in response: " + str(jdata))
            result_acc.set_success(False)
        if not '_id' in jdata:
            result_acc.add_report_line("didn't get back _id in response")
            result_acc.set_success(False)
    else:
        result_acc.add_report_line("create_entry with reply='whole' failed")
        result_acc.set_success(False)

    dto2 = SimplestDTO(message='k')
    dto_lst = [dto1, dto2]

    resp12_id = crud_client.response_of_bulk_create_entries(dto_lst, reply='id')
    if resp12_id.did_succeed():
        jdata = resp12_id.get_data_payload_as_jdata()
        if not 'created_ids' in jdata:
            result_acc.add_report_line("didn't get back created_id in response")
            result_acc.set_success(False)
    else:
        result_acc.add_report_line("create_entry with reply='id' failed")
        result_acc.set_success(False)

    resp12_count = crud_client.response_of_bulk_create_entries(dto_lst, reply='count')
    if resp12_count.did_succeed():
        jdata = resp12_count.get_data_payload_as_jdata()
        if not (('num_created' in jdata) and (jdata['num_created'] == 2)):
            result_acc.add_report_line("didn't get back num_created=2 in response")
            result_acc.set_success(False)
    else:
        result_acc.add_report_line("create_entry with reply='count' failed")
        result_acc.set_success(False)

 
    resp12_whole = crud_client.response_of_bulk_create_entries(dto_lst, reply='whole')
    if resp12_whole.did_succeed():
        jdata = resp12_whole.get_data_payload_as_jdata()
        if not (('num_created' in jdata) and (jdata['num_created'] == 2)):
            result_acc.add_report_line("didn't get back num_created=2 in 'whole' response")
            result_acc.set_success(False)

        if not 'created_entries' in jdata:
            result_acc.add_report_line("didn't get back 'created_entries' in 'whole' response")
            result_acc.set_success(False)
            return

        createds = jdata['created_entries']

        if not (('message' in createds[0]) and (createds[0]['message'] == 'j')):
            result_acc.add_report_line("didn't get back whole entry in response")
            result_acc.set_success(False)
        if not '_id' in createds[0]:
            result_acc.add_report_line("didn't get back _id in response")
            result_acc.set_success(False)
            
        if not (('message' in createds[1]) and (createds[1]['message'] == 'k')):
            result_acc.add_report_line("didn't get back whole entry in response")
            result_acc.set_success(False)
        if not '_id' in createds[1]:
            result_acc.add_report_line("didn't get back _id in response")
            result_acc.set_success(False)

    else:
        result_acc.add_report_line("create_entry with reply='whole' failed")
        result_acc.set_success(False)
  
    return 


