import os
import flask
from nest_py.core.flask.nest_endpoints.nest_endpoint import NestEndpoint
from nest_py.core.data_types.nest_id import NestId
import nest_py.knoweng.data_types.projects as projects


PIPELINE_TO_PREFIX = {
    'sample_clustering': 'nest-sc-',
    'feature_prioritization': 'nest-fp-',
    'gene_set_characterization': 'nest-gsc-',
    'phenotype_prediction': 'nest-pp-',
    'spreadsheet_visualization': 'nest-ssv-',
    'signature_analysis': 'nest-sa-'
}

class JobDownloadsEndpoint(NestEndpoint):

    def __init__(self, jobs_db_client, authenticator):
        """
        """
        self.userfiles_dir = flask.current_app.config['USERFILES_DIR']
        self.jobs_db_client = jobs_db_client
        rel_url = 'job_downloads'
        super(JobDownloadsEndpoint, self).__init__(rel_url, authenticator)
        return

    def get_flask_rule(self):
        rule = 'job_downloads/<int:job_id>'
        return rule

    def get_flask_endpoint(self):
        return 'job_downloads'

    def do_GET(self, request, requesting_user, job_id):
        nid = NestId(job_id)
        job_tle = self.jobs_db_client.read_entry(nid, user=requesting_user)
        job_dict = job_tle.get_data_dict()
        # TODO better way of determining data directory
        # will soon need API to expose a set of available downloads per job, so in
        # the meantime, not attempting anything grand here
        project_id = job_tle.get_value('project_id')
        project_path = projects.project_dirpath(self.userfiles_dir, project_id)
        dir_prefix = PIPELINE_TO_PREFIX[job_dict[u'pipeline']]
        job_slug = NestId(job_id).to_slug()
        job_dir = [d for d in os.listdir(project_path) if d.startswith(dir_prefix)\
            and job_slug.lower() in d][0]
        job_path = os.path.join(project_path, job_dir)
        trimmed_jobname = job_dict[u'name'].strip().replace(" ", "_")
        user_filename = trimmed_jobname + '.zip'
        return flask.send_from_directory(job_path, 'download.zip', \
            as_attachment=True, attachment_filename=user_filename)
