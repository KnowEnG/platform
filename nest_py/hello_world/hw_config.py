
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
            'username': 'demouser',
            'password': 'GARBAGESECRET',
            'given_name': 'ARI',
            'family_name': 'User',
            'origin': origin,
            'is_superuser': False
        },{
            'username': 'adminuser',
            'password': 'GARBAGESECRET',
            'given_name': 'Ari',
            'family_name': 'Admin',
            'origin': origin,
            'is_superuser': True
        },
        ]
    return users
