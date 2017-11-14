"""
classes for running bash commands (and bash commands over ssh) with
proper permissions and consistent error handling.

see container_users.py for making commandrunners for root and
the current docker host user.  
"""
import os
import subprocess
from StringIO import StringIO
from nest_py.ops.ops_logger import log

class BashResult(object):
    """
    When a command is run at the commandline, this is a container
    of the data collected (stdout, stderr, exit_code)
    """

    def __init__(self, command_str, exit_code, text_output):
        """
        command_str (String) command that was run
        exit_code (int) what was returned by the bash command
        text_output (string) stdout from when the command was run,
            (normally interleaved with stderr)
        """
        self.command = command_str
        self.exit_code = exit_code
        self.output = text_output.strip()
        return

    def get_exit_code(self):
        """
        """
        return self.exit_code

    def succeeded(self):
        return (self.exit_code == 0)

    def get_output(self):
        """
        full text output of stdout. probably also includes stderr
        although that is up to the CommandRunner that ran the command
        """
        return self.output

    def __str__(self):
        s = " command: " + self.command
        s += "\n exit_code: " + str(self.exit_code)
        s += "\n stdout/stderr: " + self.output
        return s


class CommandRunnerLocal(object):
    """
    Runs a bash command as a specific user and group on the container or machine
    the current python process is running in.
    """

    def __init__(self, container_user, working_dir=None):

        self.user = container_user.get_user_name()
        self.group = container_user.get_user_group()
        self.container_user = container_user
        self.env_variables = dict()

        if working_dir is None:
            self.working_dir = os.getcwd()
        else:
            self.working_dir = working_dir
        return

    def set_working_dir(self, new_cwd):
        """
        this does not change the cwd of the current process. all
        commands that are run via this runner will be run from this
        directory individually
        """
        self.working_dir = new_cwd
        return

    def add_env_variables(self, env_vars):
        self.env_variables.update(env_vars)
        return

    def run(self, bash_cmd, stream_log=False, interactive=False):
        """
        Run a bash command as the current user, in this object's
        working_dir.

        If log=True, the contents of stdout will be streamed to 
        nest_ops.logger as the command runs. If false, the output
        will be supressed but will be available in the 'output' field
        of the returned BashResult

        If interactive=True, will allow the user to interact
        through the terminal.

        Returns BashResult
        """
        full_cmd = self._build_full_command(bash_cmd)
        result = self._exec(full_cmd, stream_log, interactive)
        return result

    def _exec(self, bash_cmd, stream_log, interactive):
        """
        Actually runs a bash cmd as is. Always captures stdout and stderr
        and saving it in the returned BashResult. Optionally also prints
        the output as it occurs (stream_log=True)

        This was a huge pain to get working. Be careful if you touch this.
        """
        if interactive:
            #TODO: this works but always returns an error code
            #I don't think it matters that interactive commands 
            #can't have their stdout captured
            text_output = ''
            exit_code = os.system(bash_cmd)
        else:
            p = subprocess.Popen(bash_cmd, 
                shell=True, 
                bufsize=1,
                stderr=subprocess.STDOUT,
                stdout=subprocess.PIPE)

            text_buffer = StringIO()
            for line in iter(p.stdout.readline, b''):
                if stream_log:
                    isolated_line = line.strip() #get rid of trailing newline
                    log(isolated_line)
                text_buffer.write(line)
            p.stdout.close()
            text_buffer.flush()
            p.wait()
            exit_code = p.returncode
            text_output = text_buffer.getvalue()
            text_buffer.close()
        result = BashResult(bash_cmd, exit_code, text_output)
        #log(str(result))
        return result

    def _build_full_command(self, bash_cmd):
        """
        given a bash command (str) that you actually want to run,
        wrap it in a sudo call that makes it run with this
        CommandRunner's user, group, and working dir.
        """
        full_cmd = "sudo" 
        full_cmd += " --preserve-env"
        full_cmd += " --set-home --user=" + self.user
        full_cmd += " --group=" + self.group
        full_cmd += " bash -c "
        full_cmd += "'cd " + self.working_dir + "; "
        for k in self.env_variables:
            full_cmd += k + '=' + self.env_variables[k] + ' '
        full_cmd += bash_cmd + "'"
        return full_cmd

class CommandRunnerRemote(object):
    """
    Run a command on another machine using ssh.

    The intended scenario is something like:
        - this python process is running in the nest_ops container
        - the host_user pgroves has been cloned into the nest_ops container by
            container_users.make_host_user_command_runner()
        - the start_nest_ops.sh script has mounted my (pgroves) ssh keys
            into the container
        - The local_runner is using the pgroves user inside the container
        - A shared machine like hello-world-demo.visari.org has a user
          'nestbot', and my ssh keys are in the authorized_keys list. Currently,
          mb, pg, and xx have their keys in the nestbot account for all shared
          machines in Nebula.
        - To run the commands on hello-world-demo, an ssh command is run
          locally as pgroves, which in turn runs the deployment commands as nest_bot
          on the remote machine.
    """
    
    def __init__(self, local_runner, remote_site, remote_user_name, 
        remote_working_dir=None):
        """
        local_runner (CommandRunnerLocal) a command runner for the linux
            environment this python process is in. CommandRunnerRemote will
            run ssh commands from the CommandRunnerLocal.
        remote_site (NestSite)
        remote_user_name (string) a linux username on the remote_site machine. The
            user of local_runner must be able to log into the remote_site under
            this username using ssh keys. 
        remote_working_dir (string) moveable current working directory on
            the remote machine
        """
        self.local_runner = local_runner
        self.remote_site = remote_site
        self.remote_user = remote_user_name
        self.mounted_ssh_key = '/ssh/id_rsa'
        self.ssh_config_fn = '/ssh/config'
        if remote_working_dir == None:
            self.remote_working_dir = "~/"
        else:
            self.remote_working_dir = remote_working_dir
        return

    def set_remote_working_dir(self, new_cwd):
        """
        """
        self.remote_working_dir = new_cwd
        return

    def run(self, remote_bash_command_str):
        """
        run a bash command from the current python process as
        the remote user on the remote machine, in the remote working_dir

        This will be accomplished by running an ssh command from
        the local machine (probably nest_ops container), as
        the local user, in the local working_dir

        """
        #log("Executing command: " + str(remote_bash_command_str))
        ssh_cmd = self._build_full_ssh_cmd(remote_bash_command_str)
        log("Executing as remote command: " + str(ssh_cmd))
        res = self.local_runner.run(ssh_cmd)
        #log('Last command exit code: ' + str(res.get_exit_code()))
        return res

    def _build_full_ssh_cmd(self, remote_bash_command_str):
        """
        create the ssh prefix for the command and prepend it to the
        bash command to run on the other machine.

        Format is:
         ssh -i /ssh/id_rsa <remote_user>@<hostname> <bash_cmd>
        """
        server_address = self.remote_site.get_server_ip_address()
        #the private ssh key that is in the ssh directory mounted to the 
        #nest_ops container in start_nest_ops_container.sh
        ssh_user = self.remote_user
        ssh_prefix = 'ssh -i ' + self.mounted_ssh_key 
        ssh_prefix += ' -F ' + self.ssh_config_fn + ' '
        ssh_prefix += ssh_user + '@' +  server_address + ' '
        ssh_prefix+= " \"cd " + self.remote_working_dir + "; "
        ssh_cmd = ssh_prefix + remote_bash_command_str + "\""
        return ssh_cmd


