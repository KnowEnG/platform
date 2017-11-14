
def generate_project_params(runlevel):
    """
    configs to use in addition to the core config 
    in nest_py.core.nest_config
    """
    config = dict()

    return config

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
