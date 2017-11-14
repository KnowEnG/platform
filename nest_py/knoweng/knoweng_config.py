        
def generate_project_params(runlevel):
    
    params = {
        # used by custom knoweng endpoints
        'API_PREFIX': 'api/v2/',

        # maximum upload size in bytes
        'MAX_CONTENT_LENGTH': 250 * 1024 * 1024,

        # limits on jobs, files (TODO tie these to account types)
        'MAX_FILES_TOTAL_BYTES_PER_USER': 5 * 1024 * 1024 * 1024,
        'MAX_JOBS_TOTAL_PER_USER': 40,
        'MAX_JOBS_RUNNING_PER_USER': 5,
        
        # fill in the following configuration values to enable HubZero authentication
        'HUBZERO_APPLICATION_HOST': 'FIXME',
        'HUBZERO_DATABASE_HOST': 'FIXME',
        'HUBZERO_DATABASE_USERNAME': 'FIXME',
        'HUBZERO_DATABASE_PASSWORD': 'FIXME',
        'HUBZERO_DATABASE_NAME': 'FIXME'
    }
    return params

def generate_project_users(runlevel):
    origin = 'nest'
    users = [
        {
            'username': 'fakeuser',
            'password': 'GARBAGESECRET',
            'given_name': 'Fake',
            'family_name': 'User',
            'origin': origin,
            'is_superuser': False
        },{
            'username': 'fakeadmin',
            'password': 'GARBAGESECRET',
            'given_name': 'Fake',
            'family_name': 'Admin',
            'origin': origin,
            'is_superuser': True
        },
        ]
    return users
