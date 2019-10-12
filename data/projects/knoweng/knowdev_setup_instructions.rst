======================================================
Installing Nest on a New VM in the Knowdev Environment
======================================================

Step 1: Connect to your knowdev VM
----------------------------------
Start from the terminal in another VM. You'll need the pem file for the new
knowdev VM stored under ~/.ssh. Run the following: ::

    # replace the text in angle brackets on the next line
    KNOWDEV='<your knowdev host name; e.g., knowdev1>'
    scp -i ~/.ssh/$KNOWDEV.pem ~/.ssh/$KNOWDEV.pem ubuntu@$KNOWDEV.knoweng.org:/home/ubuntu/
    ssh -i ~/.ssh/$KNOWDEV.pem ubuntu@$KNOWDEV.knoweng.org

Step 2. Start cloud9 on your knowdev VM
---------------------------------------
From the prompt in your knowdev VM, switch to the root user: ::

    sudo su
    
Before continuing, verify you're in /home/ubuntu. Then run the following: ::

    # replace the text in angle brackets on the next few lines
    git clone https://<your bitbucket username>@bitbucket.org/arivisualanalytics/nest.git
    export CLOUD9_USERNAME=<the user name you want to use for cloud9>
    export CLOUD9_PASSWORD=<the password you want to use for cloud9>
    export HOME=/home/ubuntu
    nest/docker/start_cloud9_container.sh
    exit

Step 3. Build the application
-----------------------------
Open http://<your knowdev host name; e.g., knowdev1>.knoweng.org:8001/ in your
browser and sign in with the username and password you set in step 2.

From a cloud9 terminal, ssh back to your knowdev host: ::

    # replace the text in angle brackets on the next line
    KNOWDEV='<your knowdev host name, as above>'
    ssh -i $KNOWDEV.pem ubuntu@$KNOWDEV.knoweng.org
    sudo su
    cd nest/docker
    sh build_nest_ops.sh && cd .. && ./nest_ops docker build && ./nest_ops compile --code_type=web_assets --project=knoweng

The last command will take 30 minutes or more to run.

Step 4. Set up data for analytics
---------------------------------
Once step 3 has finished running, your cloud9 terminal should show that your
working directory is /home/ubuntu/nest. From that directory, run the following: ::

    sh data/projects/knoweng/configure.sh
    ./nest_ops docker startup --project=knoweng
    ./nest_ops db ensure_tables --project=knoweng
    ./nest_ops seed_users --project=knoweng
    ./nest_ops seed --project=knoweng
