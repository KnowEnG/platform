import os

def generate_project_params(runlevel):

    # fill in the following configuration values to enable cilogon authentication
    # the client id and client secret are provided by cilogon support
    # the redirect uri must match the public url of the index page
    # (e.g., https://platform.knoweng.org/static/index.html), use https
    # transport, and be registered with cilogon support
    cilogon_enabled = False
    cilogon_client_id = 'FIXME'
    cilogon_client_secret = 'FIXME'
    cilogon_redirect_uri = 'FIXME'

    params = {
        # used by custom knoweng endpoints
        'API_PREFIX': 'api/v2/',

        # maximum upload size in bytes
        'MAX_CONTENT_LENGTH': 250 * 1024 * 1024,

        # limits on jobs, files (TODO tie these to account types)
        'MAX_FILES_TOTAL_BYTES_PER_USER': 5 * 1024 * 1024 * 1024,
        'MAX_JOBS_TOTAL_PER_USER': 40,
        'MAX_JOBS_RUNNING_PER_USER': 5,

        'CILOGON_ENABLED': cilogon_enabled,
        'CILOGON_CLIENT_ID': cilogon_client_id,
        'CILOGON_CLIENT_SECRET': cilogon_client_secret,
        'CILOGON_REDIRECT_URI': cilogon_redirect_uri,
        'CILOGON_LOGIN_URL': \
            'https://cilogon.org/authorize?response_type=code&client_id=' + \
            cilogon_client_id + '&redirect_uri=' + cilogon_redirect_uri + \
            '&scope=openid+profile+email'
    }
    return params

def generate_project_users(runlevel):
    # Expected encoding: 'fakeuser:GARBAGESECRET:False;fakeadmin:GARBAGESECRET:True'
    users_encoded = os.getenv('SEED_USERS', 'fakeuser:GARBAGESECRET:False;fakeadmin:GARBAGESECRET:True')

    users = []
    origin = 'nest'
    
    # Do not seed static users in production, or if no SEED_USERS specified
    if runlevel == 'production':
        return users
    elif users_encoded == '':
        return users
    else:
        try:
            users_str_arr = users_encoded.split(';')
            for user_str in users_str_arr:
                user_fields = user_str.split(':')
                user_name = "fakeuser"
                user_pass = "GARBAGESECRET"
                is_su = False
                if len(user_fields) == 0:
                   print('improperly encoded user_str... skipping: ' + user_str)
                   continue
                if len(user_fields) >= 1:
                   user_name = user_fields[0]
                if len(user_fields) >= 2:
                   user_pass = user_fields[1]
                if len(user_fields) >= 3:
                   if user_fields[2] == 'True':
                       is_su = True
                users.append({
                    'username': user_name,
                    'password': user_pass,
                    'given_name': 'Fake',
                    'family_name': "Admin" if is_su else "User",
                    'origin': origin,
                    'is_superuser': is_su
                })
        except ValueError:
            print('improperly encoded SEED_USERS: ' + users_encoded)
    return users

