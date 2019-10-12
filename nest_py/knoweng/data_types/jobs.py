from nest_py.core.data_types.tablelike_schema import TablelikeSchema

COLLECTION_NAME = 'jobs'

def generate_schema():
    """
    """
    pipelines = ['sample_clustering', 'feature_prioritization', \
        'gene_set_characterization', 'phenotype_prediction']
    status_states = ['running', 'completed', 'failed']

    schema = TablelikeSchema(COLLECTION_NAME)
    schema.add_categoric_attribute('name')
    schema.add_categoric_attribute('notes')
    schema.add_foreignid_attribute('project_id')
    schema.add_categoric_attribute('pipeline', valid_values=pipelines)
    schema.add_categoric_attribute('status', valid_values=status_states)
    schema.add_categoric_attribute('error')
    schema.add_categoric_attribute('_created')
    schema.add_categoric_attribute('_updated')
    schema.add_jsonb_attribute('parameters')
    schema.add_boolean_attribute('favorite')
    return schema

#def jobs_dirpath(userfiles_dir, project_id):
#    project_dir = projects.project_dirpath(userfiles_dir, project_id)
#    files_dirpath = os.path.join(project_dir, 'files')
#    return files_dirpath
#
#def job_dirpath(userfiles_dir, project_id, job_id):
#    jobs_dir = jobs_dirpath(userfiles_dir, project_id)
#    job_path = os.path.join(jobs_dir, job_id.to_slug())
#    return job_path
#
#def job_results_dirpath(userfiles_dir, project_id, job_id):
#    job_dir = job_dirpath(userfiles_dir, project_id, job_id)
#    results_dir = os.path.join(job_dir, 'results')
#    return results_dir
#
