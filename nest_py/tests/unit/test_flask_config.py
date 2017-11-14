# -*- coding: utf-8 -*-
import pytest
import nest_py.nest_envs as nest_envs
from nest_py.nest_envs import ProjectEnv, RunLevel
import nest_py.core.nest_config as nest_config

def test_all_config_combos():
    """
    just making sure they can all be generated
    """
    all_project_names = nest_envs.VALID_PROJECT_NAMES
    all_run_levels = nest_envs.VALID_RUNLEVEL_NAMES

    for project_name in all_project_names:
        project_env = ProjectEnv(project_name)
        for run_level in all_run_levels:
            run_env = RunLevel(run_level)
            config = nest_config.generate_config(project_env, run_env)
    return

