import time
from nest_py.core.api_clients.api_client_maker import ApiClientMaker
from nest_py.core.api_clients.tablelike_api_client_maker import TablelikeApiClientMaker
from nest_py.core.api_clients.crud_api_client import CrudApiClient
from nest_py.core.data_types.tablelike_entry import TablelikeEntry

import nest_py.knoweng.data_types.jobs as jobs
import nest_py.knoweng.data_types.projects as projects

class JobsApiClientMaker(ApiClientMaker):

    def __init__(self):
        name = jobs.COLLECTION_NAME
        super(JobsApiClientMaker, self).__init__(name)
        return

    def get_crud_client(self, http_client):
        api_transcoder = jobs.generate_schema()
        ac = CrudApiClient(http_client, self.name, api_transcoder)
        return ac

    def run_smoke_scripts(self, http_client, result_acc):
        job_client = self.get_crud_client(http_client)
        smoke_job_0(http_client, result_acc, job_client)
        return

def smoke_job_0(http_client, result_acc, job_client):
    """
    http_client(NestHttpClient)

    """
    result_acc.add_report_line('BEGIN smoke_job_0()')
    project_schema = projects.generate_schema()
    job_schema = jobs.generate_schema()
    project_client = TablelikeApiClientMaker(project_schema).get_crud_client(http_client)

    project_tle_0 = TablelikeEntry(project_schema)
    project_tle_0.set_value('name', 'smoke test project')

    project_tle_1 = project_client.create_entry(project_tle_0)
    project_nest_id = project_tle_1.get_nest_id()

    job_tle_0 = TablelikeEntry(job_schema)
    job_tle_0.set_data_dict({
        u'name': u'smoke job',
        u'notes': u'created by knoweng smoke test',
        u'favorite': True,
        u'project_id': project_nest_id,
        u'pipeline': u'gene_set_characterization',
        u'status': u'running',
        u'error': None,
        u'_created': None,
        u'_updated': None,
        u'parameters': {u'a': 1, u'method': u'two'}})
    job_tle_1 = job_client.create_entry(job_tle_0)
    if job_tle_1 is None:
        result_acc.add_report_line("ERROR: create_entry failed")
        result_acc.set_success(False)
        return
    job_nest_id = job_tle_1.get_nest_id()
    result_acc.add_report_line("created entry with id: " + str(job_nest_id))

    job_observed = job_client.read_entry(job_nest_id)
    #the timestamps will have real strings in them, so set them to None to test
    job_observed.set_value('_created', None)
    job_observed.set_value('_updated', None)
    if not job_observed == job_tle_1:
        result_acc.add_report_line("ERROR: jobs didn't match")
        result_acc.add_report_line('expected: ' + str(job_tle_1))
        result_acc.add_report_line('observed: ' + str(job_observed))
        result_acc.set_success(False)

    job_tle_2 = TablelikeEntry(job_schema)
    job_tle_2.set_data_dict(job_tle_0.get_data_dict().copy())

    job_tle_2.set_value(u'status', u'completed')
    job_tle_2.set_value('_created', None)
    job_tle_2.set_value('_updated', None)
    # test __eq__ and __ne__ definitions
    if job_tle_1 == job_tle_2:
        result_acc.add_report_line("ERROR: job_1 == job_2 returned True")
        result_acc.set_success(False)
    if job_tle_1 != job_tle_2:
        pass
    else:
        result_acc.add_report_line("ERROR: job_1 != job_2 returned False")
        result_acc.set_success(False)

    # wait for job runner to mark the job failed
    max_time = time.time() + 60 # seconds
    jobs_observed = job_client.read_entry(job_nest_id)
    new_status = job_observed.get_data_dict()[u'status']
    while (not new_status == u'failed') and time.time() < max_time:
        job_x = job_client.read_entry(job_nest_id)
        new_status = job_x.get_value(u'status')
        print(' status: ' + new_status)
        time.sleep(5) # seconds

    if new_status == u'failed':
        result_acc.add_report_line("job runner marked job failed, as expected")
    else:
        result_acc.add_report_line("ERROR: job runner did not mark job failed")
        result_acc.set_success(False)

    job_3_tle = job_client.update_entry(job_nest_id, job_tle_2)
    if job_3_tle is None:
        result_acc.add_report_line("ERROR: couldn't update what we just created")
        result_acc.set_success(False)
    else:
        result_acc.add_report_line("updated what we just created: " + \
            str(job_3_tle))

        # get again
        job_observed = job_client.read_entry(job_nest_id)
        job_observed.set_value('_created', None)
        job_observed.set_value('_updated', None)
        if not job_observed == job_tle_2:
            result_acc.add_report_line("ERROR: jobs didn't match")
            result_acc.add_report_line('expected: ' + str(job_tle_2))
            result_acc.add_report_line('observed: ' + str(job_observed))
            result_acc.set_success(False)

    updated_id = job_3_tle.get_nest_id()
    job_deleted_id = job_client.delete_entry(updated_id)
    if job_deleted_id is None:
        result_acc.add_report_line("ERROR: couldn't delete job we just created")
        result_acc.set_success(False)
    else:
        result_acc.add_report_line("deleted job we just created: " + str(job_nest_id))

    project_deleted_id = project_client.delete_entry(project_nest_id)
    if project_deleted_id is None:
        result_acc.add_report_line("ERROR: couldn't delete project we just created")
        result_acc.set_success(False)
    else:
        result_acc.add_report_line("deleted project we just created: " + str(project_nest_id))

    result_acc.add_report_line('END smoke_job_0()')
    return

