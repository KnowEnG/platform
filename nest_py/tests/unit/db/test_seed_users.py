
import nest_py.core.db.db_ops_utils as db_ops_utils
import nest_py.core.nest_config as nest_config

from nest_py.nest_envs import ProjectEnv
from nest_py.nest_envs import RunLevel

import nest_py.tests.unit.db.test_users as test_users


def test_hello_world_seed_users():
    project_env = ProjectEnv.hello_world_instance()
    _test_seed_users_for_project(project_env)
    return

def test_omix_seed_users():
    project_env = ProjectEnv.mmbdb_instance()
    _test_seed_users_for_project(project_env)
    return

def test_knoweng_seed_users():
    project_env = ProjectEnv.knoweng_instance()
    _test_seed_users_for_project(project_env)
    return

def _test_seed_users_for_project(project_env):

    test_users.setup_db()
    runlevel = RunLevel.development_instance()
    db_ops_utils.seed_users(project_env, runlevel)

    user_configs = nest_config.generate_seed_users(project_env, runlevel)
    assert(len(user_configs) > 0)

    users_client = test_users.make_users_db_client()
    print("DB CLIENT USER: " + str(users_client.requesting_user))

    #an empty filter dict should return all entries in the db
    all_user_tles = users_client.simple_filter_query({})
    assert(not all_user_tles is None)

    #the +1 is for the system_user which is hardcoded, not part of configs
    assert(len(all_user_tles) == (len(user_configs) + 1))

    #running again, it should detect them and not do anything
    assert(db_ops_utils.seed_users(project_env, runlevel))
    test_users.finish_up()
    return
