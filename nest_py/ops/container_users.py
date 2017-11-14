"""
utilities for switching between predefined users *inside* the
current container (usually nest_ops).

Mainly for switching between root and the "host user" while inside
the container.

The host user does not initially exist inside the container, but docker run
can fake the user by giving an 'id' not a username. In this case you
can run commands that generate files with the host user id but
if you type 'whoami' it will say it doesn't know.

With the make_host_user_container_user() method below, a user with
the same username and uid will be created *inside* the container before returning
a CommandRunner object tied to that account. This user's default group
will be 'docker'.

Becoming the host user is useful for operations that generate files, like
compiling. When viewed from the host, these files will look like they were
made by whatever user ran the nest_ops command. Also, using the uid during
during 'docker run' can cause problems for programs that need a real user
account.  ssh needs a real user account from inside the container, for
instance, or it will refuse to run.

Becoming root is the default for docker, and allows you to run commands
that need privileges
Note that the nest_ops container is launched as root in 
start_nest_ops_container, so the 'root' runner can be considered the 
default CommandRunnerLocal.
"""
from nest_py.ops.ops_logger import log
import os
import nest_py.ops.command_runner as command_runner
from nest_py.ops.command_runner import CommandRunnerLocal

class ContainerUser(object):

    def __init__(self, user_name, user_group, uid, gid):
        """
        This simply stores the data on a user that 
        exists in the current linux environment (that
        this process is running in).

        user_name (string) a linux username
        user_group (string) a linux user group
        uid (int) the numeric user id of user_name
        gid (int) the numeric group id of user_group
        """
        self.user_name = user_name
        self.user_group = user_group
        self.uid = uid
        self.gid = gid
        return

    def get_user_name(self):
        return self.user_name

    def get_user_group(self):
        return self.user_group

    def get_uid(self):
        return self.uid

    def get_gid(self):
        return self.gid

def make_root_container_user():
    #supposedly root is always 0, 0
    #http://superuser.com/questions/626843/does-the-root-account-always-have-uid-gid-0
    uid = 0
    gid = 0
    user_name = 'root'
    user_group = 'root'
    user = ContainerUser(user_name, user_group, uid, gid)
    return user

def make_host_user_container_user():
    """
    create a user on the system that is a clone of
    the user that called the nest_ops command that launched us.

    relies on $DOCKER_HOST_USER_ID $DOCKER_HOST_USER_NAME, and
    $DOCKER_HOST_DOCKER_GROUP_ID being set
    as env variables for the container as they are in
    docker/start_nest_ops_container.sh
    """
    host_user_name = os.environ.get('DOCKER_HOST_USER_NAME')
    host_user_id = int(os.environ.get('DOCKER_HOST_USER_ID'))
    host_docker_id= int(os.environ.get('DOCKER_HOST_DOCKER_GROUP_ID'))
    user_group = 'docker'

    if not _docker_group_exists():
        _make_docker_group_inside_container(host_docker_id)

    if not _user_exists(host_user_name):
        _make_user_inside_container(host_user_name, host_user_id)

    user = ContainerUser(host_user_name, user_group, host_user_id, 
        host_docker_id)
    return user

def make_host_user_command_runner():
    """
    returns a CommandRunnerLocal to run a as a user that is
    a clone of the user calling nest_ops commands at the
    commandline

    Note that this will create the user on the current linux
    system if it doesn't exist
    """
    user = make_host_user_container_user()
    runner = CommandRunnerLocal(user)
    return runner

def make_root_command_runner():
    """
    The nest_ops container already launches as user root, so this is
    just to make use of the CommandRunner system. It won't really 
    change the user in any meaningful way.
    """
    root_user = make_root_container_user()
    cr = CommandRunnerLocal(root_user)
    return cr


def _docker_group_exists():
    """
    whether there is a 'docker' group for users in the docker container we are in
    """
    cr = make_root_command_runner()
    res = cr.run('getent group docker')
    exists = False
    if res.get_exit_code() == 0:
        exists = True
    elif res.get_exit_code() == 2:
        exists = False
    else:
        raise Exception("Detecting group 'docker' failed:\n" + res.get_output())
    return exists

def _make_docker_group_inside_container(host_docker_group_id):
    """
    host_docker_group_id(String): the gid of the group 'docker' on
        the docker host. This method will make a group 'docker' with
        the same gid inside the container we are currently in.
    """
    cr = make_root_command_runner()
    res = cr.run('addgroup --gid ' + str(host_docker_group_id) + ' docker')
    if not res.succeeded():
        raise Exception("Failed to add group 'docker' inside the container")
    return 

def _user_exists(host_user_name):
    """
    is there a user with the given user_name in the container this
    python process is running in
    """
    cr = make_root_command_runner()
    res = cr.run('getent passwd ' + str(host_user_name))
    exists = False
    if res.get_exit_code() == 0:
        exists = True
    elif res.get_exit_code() == 2:
        exists = False
    else:
        raise Exception("Detecting user '" + host_user_name + "' failed")
    return exists

def _make_user_inside_container(host_user_name, host_user_id):
    cr = make_root_command_runner()

    #the group ids of the users in the containers aren't the same
    #as the uid, which is how they are on host machines. 
    #don't know why. This was causing 
    #problems on jenkins where the gid was already in use. we don't
    #ever use the user's gid in the container (we always use the docker
    #group's gid), so it is safe to make it a much larger number as
    #we'll never use it
    user_gid = 500 + int(host_user_id)

    #http://askubuntu.com/a/94067
    cmd = 'adduser --disabled-password --gecos \"\"' 
    cmd += ' --uid ' + str(host_user_id)  
    cmd += ' --ingroup docker ' #+ str(user_gid) 
    cmd += ' ' + host_user_name
    res = cr.run(cmd)
    if not res.succeeded():
        log(str(res))
        raise Exception("Failed to add user '" + host_user_name +  
            "' inside the container")
    #ssh complains a lot if it can't make a known_hosts file
    ssh_dir = '/home/' + host_user_name + '/.ssh'
    res = cr.run('mkdir ' + ssh_dir + '; touch ' + ssh_dir + '/known_hosts')
    #log(str(res))
    res = cr.run('chown -R ' + host_user_name + ':' + 'docker ' + ssh_dir)
    #log(str(res))
    return 

