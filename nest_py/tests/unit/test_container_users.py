import grp
import pwd
import os
import tempfile
import nest_py.ops.container_users as container_users

def test_touchfile():
    cr = container_users.make_host_user_command_runner()

    host_user = os.environ.get("DOCKER_HOST_USER_NAME")
    host_user_id = int(os.environ.get("DOCKER_HOST_USER_ID"))
    docker_gid = int(os.environ.get("DOCKER_HOST_DOCKER_GROUP_ID"))

    tmp_fn = tempfile.mktemp()

    cr.run('touch ' + tmp_fn)

    #http://stackoverflow.com/a/927890/270001
    stat = os.stat(tmp_fn)

    obs_uid = stat.st_uid
    assert(obs_uid == host_user_id)

    obs_uname = pwd.getpwuid(obs_uid)[0]
    assert(obs_uname == host_user)

    obs_gid = stat.st_gid
    assert(obs_gid == docker_gid)

    obs_group = grp.getgrgid(obs_gid)[0]
    assert(obs_group == 'docker')

    cr.run('rm ' + tmp_fn)
    return
