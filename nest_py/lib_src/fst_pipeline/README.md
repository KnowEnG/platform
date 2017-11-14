## Installation ##

The following procedure assumes you're running Ubuntu 14.04 and have cloned this repository to your machine. Open a command prompt and change your working directory to the cloned repository (fst_pipeline/, which is the directory that contains this README.md).

### Step 1: Install R ###

From the command prompt , run the following:

    echo "deb http://ftp.ussg.iu.edu/CRAN/bin/linux/ubuntu trusty/" | sudo tee -a /etc/apt/sources.list > /dev/null
    sudo apt-key adv --keyserver keyserver.ubuntu.com --recv-keys E084DAB9  
    sudo add-apt-repository ppa:marutter/rdev
    sudo apt-get update    
    sudo apt-get install r-base r-base-dev
    R

You'll be left at an R prompt. Type q() to quit R and return to the command prompt.

### Step 2: Install python and dependencies ###

From the command prompt, run the following:

    sudo apt-get install -y python2.7 python2.7-dev python-pip libevent-dev libblas-dev liblapack-dev libatlas-base-dev gfortran
    pip install -r requirements.txt
    ./fst.py setup