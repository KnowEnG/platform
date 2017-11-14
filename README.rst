===============================
Platform
===============================

This repository contains the codebase implementing the KnowEnG platform's
web services and client.


To Install Docker
-----------------

Check the current version of Docker installed on your machine ::

    docker -v

If Docker is older than 1.6 or not installed at all, follow the instructions
here to install the latest version of Docker: http://docs.docker.com/installation/ubuntulinux/  
Don't worry about the "Optional configurations for Docker on 
Ubuntu." Note that if a pre-1.6 version of Docker was installed by apt-get, 
you may need to run ::

    sudo apt-get remove docker.io

to avoid warning messages while following the instructions.

nest_ops Overview:
-----------------
nest_ops is a commandline tool that does common compilation, deployment,
docker, and maintenance tasks specific to the nest code repository.

nest_ops is implemented in python code that lives inside this repo. The
code is always run in a special 'nest_ops' docker container, although that
fact is largely hidden from the developer typing commands. Every time
nest_ops is invoked, a docker container with the necessary dependencies is
launched, runs a single python command, and exits. (Look inside
the 'nest_ops' shell script to see how the handoff is done). 

Getting Started:
----------------
On the first run, and any time python or javascript requirements change,
you will need to build the nest_ops docker container manually. All
other containers are built and run by running nest_ops commands.

First time ::

    cd docker
    sh build_nest_ops.sh
    cd ..
    chmod u+x nest_ops
    ./nest_ops -h

From then on ::

	./nest_ops <subcommand> <options>
	
Help Summary:
-------------

usage: nest_ops [-h] {compile,doc,clienttest,pytest,docker,ci,all_help} ...

Commands that operate against the code, output files to local working directory.
Docker commands build locally then deploy and start/stop on a specified host's
docker daemon.

optional arguments:
  -h, --help            show this help message and exit

  subcommands:
    {compile,doc,clienttest,pytest,docker,ci,all_help}
	    compile             Compile a type of code, or everything.
		doc                 Generate all docs and api-docs (python, typescript, etc).
		clienttest          Run all client unit tests.
		pytest              Run one or all python unit tests.
		docker              Build, Deploy, Start/Stop docker containers in the nest stack.
		ci                  Run continuous-integration tasks (build, test, deploy).
		all_help            Print all subcommands' long-form help messages

Common options and their defaults:

	<nest_site> = ['localhost':default, 'staging', 'demo']
	<project> = ['knoweng', 'mmbdb', 'hello_world':default]
	<runlevel> = ['development':default, 'production']
	

See the bottom of this file for long-from subcommand help

To Run the Web Server
---------------------

Before the first run, and whenever code requirements change, build
all docker containers:

    ./nest_ops docker --service=all build

Start the development web server and all dependencies in 'knoweng' mode::

    ./nest_ops docker --service=all --project=knoweng startup

This will start the backend. The skeleton of the website will be available at http://localhost:8000/static/index.html

If you need the frontend for real, perform the steps to Build the Web Client below to generate javascript, style sheets, etc.

Stop the development web server with ::

	./nest_ops docker --service=all teardown

For more detailed help on individual containers and additional parameters,
see:

	./nest_ops docker -h

To Build the Web Client and Run the Client Tests
------------------------------------------------
To compile TypeScript to javascript, build style sheets, fetch frontend dependencies, etc:

Run ::

	./nest_ops compile --code_type=web_assets

With the development web server running (procedure explained above), the client
will be found at http://127.0.0.1/static/index.html.

Launch all client tests with ::

    ./nest_ops clienttest


To Run the Python Tests
----------------

To run python tests, the backing services must be running:

    ./nest_ops docker --service=postgres startup
    ./nest_ops docker --service=redis startup

Then, launch all tests with ::

    ./nest_ops pytest

To run the tests of a single python module, give its filename relative
to the tests/unit/ directory. E.g., for tests in nest/tests/unit/eve_config_test.py:

	./nest_ops pytest eve_config_test.py


To Add New Python Dependencies
------------------------------

Add the pip library name and an exact version number to one or more of the 
files under ``requirements/``. (Note that some files include each other; e.g.,
``nest_flask.txt`` loads everything from ``common.txt``.) Save your changes and
run ::

	cd docker
	sh build_nest_ops.sh
	cd ..
	./nest_ops docker --service=nest_flask build   
	./nest_ops docker --service=nest_jobs build   

You'll need to stop and restart the development web server for changes to take
effect.

To Generate Documentation
-------------------------

Run ::

	./nest_ops doc

The documentation will be created in HTML format under docs/generated/_build/html.

Docstring Style
---------------

See http://sphinxcontrib-napoleon.readthedocs.org/en/latest/example_google.html


Future planning (These are not implemented)
-------------------------------------------

nest_ops integration_test --project=<project_env> --target_site=<site> --port=80
   runs the integration test suite for a given project against the nest_flask
   server running on targe_site. The tests always run from localhost (client
   calls from localhost) but the server they exercise can be a different
   machine (usually staging servers)

nest_ops database --project=<project_env> --targe_site=<site> <db-action>

	<db-action> = ['init-schemas', 'drop-schemas', 'wipe-data',  'seed-data']

nest_ops job_queue --project=<project> --target_site=<site> <job-action>
	<job-action> = ['prep-redis', 'kill-all-running', 'cancel-queued', 'wipe-history']



nest_ops -h
-------------

The below documentation is autogenerated and provides detailed usage of
nest_ops commands. Improving documenation there is better than editing this
doc directly. 

Run the following command to get the most up to date version: './nest_ops all_help'

h, --help  show this help message and exit

Autogenerated:
usage: nest_ops [-h]
                {compile,doc,clienttest,pytest,docker,smoke_test,ci,deploy,remote_maintenance,seed,seed_users,wipe,wix,db,all_help}
                ...

Commands that operate against the code, output files to local working directory.
Docker commands build locally then deploy and start/stop on a specified host's
docker daemon.

optional arguments:
  -h, --help            show this help message and exit

subcommands:
  {compile,doc,clienttest,pytest,docker,smoke_test,ci,deploy,remote_maintenance,seed,seed_users,wipe,wix,db,all_help}
    compile             Compile a type of code, or everything.
    doc                 Generate all docs and api-docs (python, typescript, etc).
    clienttest          Run all client unit tests.
    pytest              Run one or all python unit tests.
    docker               Build, Start, Stop docker containers in the nest stack.
    smoke_test          Run one or all smoke tests against a nest server.
    ci                  Run continuous-integration tasks (build, test, deploy).
    deploy              Download and run the nest stack on a remote machine
    remote_maintenance  Run maintenance script on a remote machine
    seed                Run a project's seeding script against a nest server.
    seed_users          Seed the local database with a project's pre-configured users.
    wipe                Delete all data from all eve endpoints that store data for a project
    wix                 Run a job with a config file that has been
                        registered in the command registry.
    db                  Directly manipulate a Postgres database used by Nest.
    all_help            Print all subcommands' long-form help messages

##################
### doc ###
####################

usage: nest_ops doc [-h]

Generate all docs and api-docs (python, typescript, etc).

Has no arguments. Will attempt to generate all types of docs
even if one fails.

optional arguments:
  -h, --help  show this help message and exit

##################
### compile ###
####################

usage: nest_ops compile [-h]
                        [--code_type {python,web_assets,web_assets:npm,web_assets:ts,web_assets:dist,all}]
                        [--project {hello_world,knoweng,mmbdb}]
                        [--runlevel {development,production}]

Compile a type of code, or everything.

optional arguments:
  -h, --help            show this help message and exit
  --code_type {python,web_assets,web_assets:npm,web_assets:ts,web_assets:dist,all}
                        The target code type to compile
                            python         : runs pylint with 'errors' only reporting
                            web_assets     : runs web_assets:npm, web_assets:ts, and web_assets:dist
                            web_assets:npm : (re)installs node packages
                            web_assets:ts  : compiles typescript, builds all assets
                            web_assets:dist: prepares the client/dist directory to serve the specified project's assets
                            all            : (default) all of the above
  --project {hello_world,knoweng,mmbdb}
                        Which project to build. Only affects the web_assets:dist
                                    code_type, where it determines which project's index.html
                                    will be the main entry point index.html in the static files.
  --runlevel {development,production}
                        Determines the run level for logging, error checking, etc.

##################
### clienttest ###
####################

usage: nest_ops clienttest [-h]

Run all client unit tests.

optional arguments:
  -h, --help  show this help message and exit

##################
### pytest ###
####################

usage: nest_ops pytest [-h]
                       [--spawn-linked-container [{true,false,True,False}]]
                       [python_source_file]

Run one or all python unit tests.

positional arguments:
  python_source_file    Name of a python file of unit tests relative to tests/unit/

optional arguments:
  -h, --help            show this help message and exit
  --spawn-linked-container [{true,false,True,False}]
                        
                        If true, spawn a new docker container with postgres and redis linked 
                        to run the test(s) in. Requires postgres_i and redis_i to already be 
                        running. Default is True.

##################
### docker ###
####################

usage: nest_ops docker [-h] [--project {hello_world,knoweng,mmbdb}]
                       [--site {localhost,demo.hello_world,demo.knoweng,demo.mmbdb,staging.hello_world,staging.knoweng,staging.mmbdb,klumpp.mmbdb}]
                       [--runlevel {development,production}]
                       [--service {all,postgres,redis,nest_flask,nest_jobs}]
                       [{build,startup,teardown}]

 Build, Start, Stop docker containers in the nest stack.

positional arguments:
  {build,startup,teardown}
                        
                        build:    runs 'docker build' on the Dockerfile associated with
                                   the service. All services must therefore have a Dockerfile
                                   in nest/docker/, even if they don't add anything to a
                                   publicly available image. After build, an image is available
                                   to run on localhost.
                        startup:  starts the docker container and runs its main executable
                        teardown: Stops the container and removes it from the list of
                                   inactive containers. You must remove the previously running
                                   container before starting a new one as they will try to
                                   use the same name. Note that this means all containers
                                   should be considered stateless, and must write any data
                                   that must survive startup/teardown to a docker 'volume'
                                   that maps to a file directory on the host machine.

optional arguments:
  -h, --help            show this help message and exit
  --project {hello_world,knoweng,mmbdb}
                        Which project to run the service as. Note that
                                    not all commands and services necessarily do anything
                                    unique for a project-env. Redis ignores it. The nest_flask
                                    and nest_jobs containers currently ignore it during build
                                    but then use it during 'start' so that they expose only
                                    the correct endpoints, etc. 
  --site {localhost,demo.hello_world,demo.knoweng,demo.mmbdb,staging.hello_world,staging.knoweng,staging.mmbdb,klumpp.mmbdb}
                        The environment of services that is being manipulated,
                                    either localhost or one of the known shared environments
  --runlevel {development,production}
                        Determines the run level for logging, error checking, etc.
  --service {all,postgres,redis,nest_flask,nest_jobs}
                        Which of the docker containers within the stack to manipulate.

##################
### ci ###
####################

usage: nest_ops ci [-h] {feature,develop,master}

Run continuous-integration tasks (build, test, deploy).

positional arguments:
  {feature,develop,master}
                        The type of git branch:
                            feature : unmerged feature branches. runs tests.
                            develop : mainline development branch. Runs tests then deploys to staging
                            master  : mainline stable branch. Run tests then deploy to demo
                            

optional arguments:
  -h, --help            show this help message and exit

##################
### all_help ###
####################

usage: nest_ops all_help [-h]

optional arguments:
  -h, --help  show this help message and exit
nest_ops exit_code: 0 (SUCCESS). Took: 0.0s
