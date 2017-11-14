# -*- coding: utf-8 -*-
import os
import sys
import pytest
from nest_py.ops.command_runner import CommandRunnerLocal
import nest_py.ops.container_users as container_users
from StringIO import StringIO

def test_echo():
    cr = container_users.make_root_command_runner()
    res = cr.run("echo \"hi from test_echo\"", stream_log=True)
    assert res.succeeded()
    assert (res.get_output() == 'hi from test_echo')
    return

def test_multiline():
    cr = container_users.make_root_command_runner()
    orig_stdout = sys.stdout
    capture_stdout = StringIO()
    sys.stdout = capture_stdout
    res = cr.run("echo \"line1\"", stream_log=True)
    sys.stdout.flush()
    assert (capture_stdout.getvalue().strip() == 'line1')
    assert res.succeeded()
    assert (res.get_output() == 'line1')


    res = cr.run("echo \"line2\"", stream_log=True)
    sys.stdout.flush()
    assert (capture_stdout.getvalue().strip() == 'line1\nline2')
    assert res.succeeded()
    assert (res.get_output() == 'line2')

    res = cr.run("echo \"line3\"; echo \"line4\"", stream_log=True)
    assert res.succeeded()
    assert (res.get_output() == 'line3\nline4')

    sys.stdout = orig_stdout
    return


