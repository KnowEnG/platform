
from nest_py.core.api_clients.http_client import NestHttpClient
from nest_py.ops.ops_logger import log
import subprocess
import os

VALID_NEST_SITE_NAMES = ['localhost', 'demo.hello_world', 'demo.knoweng', 'demo.mmbdb', 'staging.hello_world', 'staging.knoweng', 'staging.mmbdb', 'vpc.staging.hello_world', 'vpc.staging.mmbdb', 'vpc.demo.hello_world', 'vpc.demo.mmbdb']

DEFAULT_NEST_SITE_NAME = 'localhost'

NEST_SITE_IP = {
    'staging.hello_world': 'hello-world-staging.visari.org',
    'staging.knoweng': 'knoweng-staging.visari.org',
    'staging.mmbdb': 'omix-staging.visari.org',
    'demo.hello_world': 'hello-world-demo.visari.org',
    'demo.knoweng': 'knoweng-demo.visari.org',
    'demo.mmbdb': 'omix-demo.visari.org',

    #these are addresses within the AWS VPC. Using these
    #avoids the firewall when are within the VPC
    'vpc.staging.hello_world': 'ip-172-31-62-139.ec2.internal',
    'vpc.staging.mmbdb': 'ip-172-31-54-129.ec2.internal',
    'vpc.demo.hello_world': 'ip-172-31-59-228.ec2.internal',
    'vpc.demo.mmbdb': 'ip-172-31-56-224.ec2.internal',
}

class NestSite():
    """
    Defines one of the known locations a nest app can
    be deployed to. A NestSite maps one-to-one 
    with the url the app will be available at. In practice, normally 
    also maps directly to a single machine running the full stack. 
    E.g. (NestSite=staging,ProjectEnv=knoweng) implies a single
    url or ip address running the knoweng flavor of the nest app.
    
    Examples:

    "localhost" is whatever machine we are running on.
    "demo.hello_world" is the ncsa nebula machine running the hello_world code
        as a 'demo'
    
    Mostly parsing and error checking for reading OS environment variable.

    #TODO: this is very similar to ProjectEnv. Refactor if any more env types
    are added
    """

    def __init__(self, site_name=DEFAULT_NEST_SITE_NAME):
        """
        """
        if site_name not in VALID_NEST_SITE_NAMES:
            msg = "Invalid target site name: '" + str(site_name)
            msg += "', valid options are: " + str(VALID_NEST_SITE_NAMES)
            raise Exception(msg)
        self.site_name = site_name
        self.ip_address = NestSite.deduce_server_address(site_name)
        return

    def write_to_os(self):
        """
        sets the NEST_TARGET_SITE environment variable in the OS shell 
        this app is running in. Mainly used to test detect_from_os()
        """
        os.environ['NEST_SITE'] = self.site_name
        return

    def get_nest_site_name(self):
        return self.site_name

    def get_server_ip_address(self):
        return self.ip_address

    def build_http_client(self, port=80):
        """
        build a NestHttpClient pointed at the nest_site server.
        """
        server = self.get_server_ip_address()
        http_client = NestHttpClient(server_address=server, server_port=port)
        return http_client

    def __str__(self):
        s = 'NEST_SITE=' + self.get_nest_site_name()
        return s

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            if self.site_name == other.site_name:
                return True
        return False

    @staticmethod 
    def from_string(env_str):
        clean_str = env_str.lower()
        if clean_str == '':
            env = None
        else:
            env = NestSite(clean_str)
        return env

    @staticmethod
    def detect_from_os(fallback_to_default=False):
        """
        Inspects the OS environment variable "NEST_SITE" to find 
        the current NEST_SITE. 
        If NEST_SITE is not set or empty string, returns None 
        If fallback_to_default=True, will return default_instance instead of None
        If NEST_SITE has an invalid value, raises an exception.
        """
        raw_env = os.environ.get("NEST_SITE")
        if raw_env is None:
            env = None
        else:
            env = NestSite.from_string(raw_env)
        if (env is None) and fallback_to_default:
            env = NestSite.default_instance()
        return env

    @staticmethod
    def localhost_instance():
        env = NestSite('localhost')
        return env

    @staticmethod
    def demo_hello_world_instance():
        env = NestSite('demo.hello_world')
        return env

    @staticmethod
    def demo_knoweng_instance():
        env = NestSite('demo.knoweng')
        return env

    @staticmethod
    def staging_hello_world_instance():
        env = NestSite('staging.hello_world')
        return env

    @staticmethod
    def staging_knoweng_instance():
        env = NestSite('staging.knoweng')
        return env

    @staticmethod
    def default_instance():
        env = NestSite(DEFAULT_NEST_SITE_NAME)
        return env

    @staticmethod
    def deduce_server_address(site_name):
        """
        returns an IP address as a string
        """
        if site_name == 'localhost':
            server_ip = NestSite.find_localhost_ip()
        elif site_name in VALID_NEST_SITE_NAMES:
            server_ip = NEST_SITE_IP[site_name]
        else:
            raise Exception("don't know about any sites except: " + 
                str(VALID_NEST_SITE_NAMES))
        return server_ip


    @staticmethod
    def find_localhost_ip():
        """
        detects address of docker container host. returns as string
        """
         #http://stackoverflow.com/questions/22944631/how-to-get-the-ip-address-of-the-docker-host-from-inside-a-docker-container
        cmd =  ["/sbin/ip", "route"]
        route_info = subprocess.check_output(cmd)
        server_ip = route_info.split(' ')[2]
        #print("Found localhost: " + str(server_ip))
        return server_ip
     


