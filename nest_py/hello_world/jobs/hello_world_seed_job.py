import os

from nest_py.core.jobs.jobs_logger import log
import nest_py.hello_world.data_types.hello_tablelike as hello_tablelike
import nest_py.hello_world.api_clients.hw_api_clients as hw_api_clients
import nest_py.core.jobs.box_downloads as box_downloads
import nest_py.ops.container_users as container_users
import nest_py.core.jobs.jobs_auth as jobs_auth
from nest_py.core.data_types.nest_id import NestId

def run(http_client, hello_world_data_dir):
    """
    hello_world_data_dir when inside a container is probably:
     /code_live/data/project/hello_world
    """
    log("hello_world_seed_job: Begin")
    exit_code = 0
    jobs_auth.login_jobs_user(http_client, 'fakeuser', 'GARBAGESECRET')
    

    x0 = hello_tablelike.HelloTablelikeDTO(1.0, 2.0, 'x',
        ['a','b'], [1.1, 2.2], NestId(0), [NestId(1), NestId(2)], 
        {'x':'innerx'}, {'xb':'innerxb'}, 5, [6,7])

    client_makers = hw_api_clients.get_api_client_makers()
    client = client_makers['hello_tablelike'].get_crud_client(http_client)

    eve_atts0 = client.create_entry(x0.to_tablelike_entry())
    if eve_atts0 is None:
        exit_code = 1 

    log('downloading test file from box')
    file_owner = container_users.make_host_user_container_user()
    abs_filename_0 = hello_world_data_dir + '/hello/box_test_0.txt'
    box_url_0 = "https://uofi.box.com/shared/static/y8a7qmgskm73rpovf16j96yr3st7ea96.txt"
    box_downloads.download_from_box_no_auth(box_url_0, abs_filename_0, 
        file_owner=file_owner, force=True)
    box_downloads.download_from_box_no_auth(box_url_0, abs_filename_0, 
        file_owner=file_owner, force=False)
    assert(os.path.isfile(abs_filename_0))
    log('verifying test download contents')
    verify_test_file_0(abs_filename_0)

    log("hello_world_seed_job: Done")
    return exit_code


def verify_test_file_0(downloaded_location):
    with open(downloaded_location) as f:
        obs_contents = f.read()
    print('obs contents:')
    print(obs_contents)
    exp_contents = "test line 0\ntest line 1\n"
    assert(exp_contents == obs_contents) 
    return
