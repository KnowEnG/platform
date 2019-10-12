
def generate_project_params(runlevel):
    """Returns the project-specific params."""
    params = {}
    return params

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
        },
        {
            'username': 'klumppuser',
            'password': 'GARBAGESECRET',
            'given_name': 'KlumppLab',
            'family_name': 'User',
            'origin': origin,
            'is_superuser': False
        },
        {
            'username': 'mayouser',
            'password': 'GARBAGESECRET',
            'given_name': 'Mayo',
            'family_name': 'Shared',
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
