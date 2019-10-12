# -*- coding: utf-8 -*-
import os
import sys
import pytest
import nest_py.wix.jobs.hello_world0 as hello_world0
from nest_py.core.jobs.file_space.wix_file_space import WixFileSpace
from nest_py.core.jobs.job_context import JobContext
from nest_py.core.data_types.nest_id import NestId
import nest_py.ops.CMD_nest_ops as CMD_nest_ops
import nest_py.ops.container_users as container_users

from nest_py.nest_envs import ProjectEnv
from nest_py.nest_envs import RunLevel
from nest_py.core.data_types.nest_id import NestId
import nest_py.tests.unit.db.test_users as test_users
import nest_py.core.db.db_ops_utils as db_ops_utils

def prep_db():
    """
    test_users has methods to point the nest_users clients to a
    different table so that any existing user entries aren't disturbed
    on the local postgres instance. We also seed the hello_world project
    users into the testing table.
    """
    test_users.setup_db()
    runlevel = RunLevel.development_instance()
    project_env = ProjectEnv.hello_world_instance()
    db_ops_utils.seed_users(project_env, runlevel)
    return

def finalize_db():
    """
    tell test_users to put the nest_users table back to normal
    """
    test_users.finish_up()
    return

def test_full_run():
    prep_db()
    cl_args = ['wix', 'hello_world.0']
    exit_code = CMD_nest_ops.main(cl_args)
    assert(exit_code == 0)
    finalize_db()
    return

def test_external_job_dirs():
    prep_db()
    job_key = 'hello_world.0'

    #TODO: the project_root_dir (that nest_ops controls) needs to
    #be available to the tests so they can find the data dir
    root_dir = '/code_live/data/wix/'
    user = container_users.make_host_user_container_user()

    wix_fs = WixFileSpace(root_dir, user)
    job_fs = wix_fs.get_job_file_space(job_key, ensure=True)

    #can we get the expected run dir from the wix_file_space?
    obs_jfs = wix_fs.get_job_file_space(job_key)
    obs_dir = obs_jfs.get_run_file_space(NestId(0), ensure=True).get_dirpath()
    print('full obs dirpath for run 000: ' + obs_dir)
    exp_dir = root_dir
    assert(os.path.exists(exp_dir))
    exp_dir = os.path.join(exp_dir, 'hello_world.0')
    assert(os.path.exists(exp_dir))
    exp_dir = os.path.join(exp_dir, 'runs')
    assert(os.path.exists(exp_dir))
    exp_dir = os.path.join(exp_dir, 'run_000')
    assert(os.path.exists(exp_dir))
    assert(os.path.isdir(exp_dir))
    assert(obs_dir == exp_dir)

    obs_dir = obs_jfs.get_dirpath()
    exp_dir = os.path.join(root_dir, 'hello_world.0')
    assert(obs_dir == exp_dir)

    obs_dir = obs_jfs.get_job_global_data_dir()
    exp_dir = os.path.join(root_dir, 'hello_world.0', 'cross_run_data')
    assert(obs_dir == exp_dir)

    finalize_db()
    return


