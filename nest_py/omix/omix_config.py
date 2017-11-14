
def generate_project_params(runlevel):
    """Returns the project-specific params."""
    params = { }
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
        },
        {
            'username': 'fakeadmin',
            'password': 'GARBAGESECRET',
            'given_name': 'Fake',
            'family_name': 'Admin',
            'origin': origin,
            'is_superuser': True
        },
        ]
    return users
