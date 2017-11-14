==========================================================
Installing Nest on a New VM in the Development Environment
==========================================================

Step 1: Connect to your development VM
--------------------------------------
Start from the terminal in another VM. You'll need the pem file for the new
development VM stored under ~/.ssh. Run the following: ::

    ssh -i ~/.ssh/mypem.pem myaccount@myvm.mydomain.com

Step 2. Build the application
-----------------------------
Make sure you're in your home directory on the development VM. Run the
following: ::

    sudo su
    git clone https://github.com/KnowEnG/platform.git
    cd platform/docker
    sh build_nest_ops.sh && cd .. && ./nest_ops docker build && ./nest_ops compile --code_type=web_assets --project=knoweng

The last command will take 30 minutes or more to run.

Step 3. Set up data for analytics
---------------------------------
Once step 2 has finished running, your terminal should show that your working
directory is the platform/ subdirectory under your home directory. Run the
following: ::

    sh data/projects/knoweng/configure.sh
    ./nest_ops docker startup --project=knoweng
    ./nest_ops db ensure_tables --project=knoweng
    ./nest_ops seed_users --project=knoweng
    ./nest_ops seed --project=knoweng
