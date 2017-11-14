===============================
Nest Frontend
===============================
This repository contains the codebase implementing both the Mayo Microbiome 
Database project and the KnowEnG frontend. 

Starting the Development Environment
------------------------------------
To quickly start-up a development environment for Nest projects, execute the following command in your SSH terminal:

    ./docker/start_cloud9_container.sh

This will start up Cloud9, a cloud-based development environment, which you can access via port 8001.

We have built a flavor of Cloud9 pre-loaded with all of the things you'll need to develop a Nest project:
* Python 2.7.6
* Node 5.8.0

Running the Unit Tests via SSH
------------------------------
Simply execute the following command:

    ./nest_ops clienttest

Running the Unit Tests via Cloud9
---------------------------------
If you are running in Cloud9, you will need to install dependencies first:

    apt-get update && apt-get -y install xvfb wget sudo && wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | sudo apt-key add - && sudo sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list' && apt-get update && apt-get -y install google-chrome-stable

This will install Xvfb and Google Chrome stable into your Cloud9 container.

You can then run the following command directly from your Cloud9 terminal to execute the tests:

    cd /workspace/nest/client
    gulp test

This will use the Karma test runner to run the unit test specs located in src/ or dist/.

NOTE: The test runner will count any file as a test case if it is within the directory **client/src/** AND ends with the .spec.ts or .spec.js extension.
