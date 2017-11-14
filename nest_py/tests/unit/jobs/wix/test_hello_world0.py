# -*- coding: utf-8 -*-
import os
import sys
import pytest
import nest_py.wix.jobs.hello_world0 as hello_world0
from nest_py.core.jobs.job_file_space import JobRunFileSpace
from nest_py.core.jobs.job_context import JobContext
import nest_py.ops.CMD_nest_ops as CMD_nest_ops
import nest_py.ops.container_users as container_users

from nest_py.nest_envs import ProjectEnv
from nest_py.nest_envs import RunLevel
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
    #run hello_world.0 to guarantee there is a zero-th job
    job_key = 'hello_world.0'
    cl_args = ['wix', job_key]
    exit_code = CMD_nest_ops.main(cl_args)

    #TODO: the project_root_dir (that nest_ops controls) needs to
    #be available to the tests so they can find the data dir
    root_dir = '/code_live/data/wix/'
    user = container_users.make_host_user_container_user()
    fs = JobRunFileSpace(root_dir, job_key, user)
    config = dict()
    jcx = JobContext(job_key, user, fs, config)

    obs_dir = jcx.get_external_run_dir(job_key, 0)
    exp_dir = os.path.join(root_dir, 'hello_world.0/run_000')
    assert(os.path.exists(exp_dir))
    assert(os.path.isdir(exp_dir))

    assert(obs_dir == exp_dir)

    finalize_db()
    return


