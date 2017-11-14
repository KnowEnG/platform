#The nest app supports different 'dimensions' of it's environment.
#At the very least, which project (knoweng, mmbdb, etc) and what
#runlevel (development, production)
import os

VALID_PROJECT_NAMES = ['hello_world', 'knoweng', 'mmbdb']
DEFAULT_PROJECT_NAME = 'hello_world'

VALID_RUNLEVEL_NAMES = ['development', 'production']
DEFAULT_RUNLEVEL_NAME = 'development'

class ProjectEnv(object):
    """
    Define keys for specifying the active project ('mmbdb', 'knoweng', etc).
    Mostly parsing and error checking for reading OS environment variable.
    """

    def __init__(self, project_name=DEFAULT_PROJECT_NAME):
        """
        """
        if project_name not in VALID_PROJECT_NAMES:
            msg = "Invalid project name: '" + str(project_name)
            msg += "', valid options are: " + str(VALID_PROJECT_NAMES)
            raise Exception(msg)
        self.project_name = project_name
        return

    def write_to_os(self):
        """
        sets the PROJECT_ENV environment variable in the OS shell
        this app is running in. Mainly used to test detect_from_os()
        """
        os.environ['PROJECT_ENV'] = self.project_name
        return

    def get_project_name(self):
        return self.project_name

    def __str__(self):
        s = 'PROJECT_ENV=' + self.get_project_name()
        return s

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            if self.project_name == other.project_name:
                return True
        return False

    @staticmethod
    def from_string(env_str):
        clean_str = env_str.lower()
        if clean_str == '':
            env = None
        else:
            env = ProjectEnv(clean_str)
        return env

    @staticmethod
    def detect_from_os(fallback_to_default=False):
        """
        Inspects the OS environment variable "PROJECT_ENV" to find
        the current project_env.
        If PROJECT_ENV is not set or empty string, returns None
        If fallback_to_default=True, will return default_instance instead of None
        If PROJECT_ENV has an invalid value, raises an exception.
        """
        raw_env = os.environ.get("PROJECT_ENV")
        if raw_env is None:
            env = None
        else:
            env = ProjectEnv.from_string(raw_env)
        if (env is None) and fallback_to_default:
            env = ProjectEnv.default_instance()
        return env

    @staticmethod
    def knoweng_instance():
        env = ProjectEnv('knoweng')
        return env

    @staticmethod
    def mmbdb_instance():
        env = ProjectEnv('mmbdb')
        return env

    @staticmethod
    def hello_world_instance():
        env = ProjectEnv('hello_world')
        return env

    @staticmethod
    def default_instance():
        env = ProjectEnv(DEFAULT_PROJECT_NAME)
        return env


class RunLevel(object):
    """
    Define deployment level keys ('development', 'production'). Mostly
    parsing and error checking for reading OS environment variable.

    #TODO: this is very similar to ProjectEnv. Refactor if any more env types
    are added
    """

    def __init__(self, runlevel_name=DEFAULT_RUNLEVEL_NAME):
        """
        """
        if runlevel_name not in VALID_RUNLEVEL_NAMES:
            msg = "Invalid runlevel: '" + str(runlevel_name)
            msg += "', valid options are: " + str(VALID_RUNLEVEL_NAMES)
            raise Exception(msg)
        self.runlevel_name = runlevel_name
        return

    def write_to_os(self):
        """
        sets the NEST_RUNLEVEL environment variable in the OS shell
        this app is running in. Mainly used to test detect_from_os()
        """
        os.environ['NEST_RUNLEVEL'] = self.runlevel_name
        return

    def get_runlevel_name(self):
        return self.runlevel_name

    def __str__(self):
        s = 'NEST_RUNLEVEL=' + self.get_runlevel_name()
        return s

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            if self.runlevel_name == other.runlevel_name:
                return True
        return False

    @staticmethod
    def from_string(env_str):
        clean_str = env_str.lower()
        if clean_str == '':
            env = None
        else:
            env = RunLevel(clean_str)
        return env

    @staticmethod
    def detect_from_os(fallback_to_default=False):
        """
        Inspects the OS environment variable "NEST_RUNLEVEL" to find
        the current NEST_RUNLEVEL.
        If NEST_RUNLEVEL is not set or empty string, returns None
        If fallback_to_default=True, will return default_instance instead of None
        If NEST_RUNLEVEL has an invalid value, raises an exception.
        """
        raw_env = os.environ.get("NEST_RUNLEVEL")
        if raw_env is None:
            env = None
        else:
            env = RunLevel.from_string(raw_env)
        if (env is None) and fallback_to_default:
            env = RunLevel.default_instance()
        return env

    @staticmethod
    def development_instance():
        env = RunLevel('development')
        return env

    @staticmethod
    def production_instance():
        env = RunLevel('production')
        return env

    @staticmethod
    def default_instance():
        env = RunLevel(DEFAULT_RUNLEVEL_NAME)
        return env


