echo "Make sure you know what this script does before you run it."
echo "Enter your UIUC netid and press enter"
read NETID

NETWORK_SHARE_BASE_PATH='/mnt/knowdev'

# create paths for analytics on network share
# creating .gitkeeps, too, so git status doesn't report them missing once we
# create the symlinks
# TODO check existence, etc., beforehand
echo "Creating directories on network share under $NETWORK_SHARE_BASE_PATH/$NETID"
mkdir $NETWORK_SHARE_BASE_PATH/$NETID
mkdir $NETWORK_SHARE_BASE_PATH/$NETID/userfiles
touch $NETWORK_SHARE_BASE_PATH/$NETID/userfiles/.gitkeep
mkdir $NETWORK_SHARE_BASE_PATH/$NETID/networks
touch $NETWORK_SHARE_BASE_PATH/$NETID/networks/.gitkeep
mkdir $NETWORK_SHARE_BASE_PATH/$NETID/logs

# copy knowledge network
# TODO download directly from S3 or have all instances share a common copy
echo "Copying knowledge network (takes a while)"
cp -r $NETWORK_SHARE_BASE_PATH/shared/userKN-20rep-1706/* $NETWORK_SHARE_BASE_PATH/$NETID/networks/

# create symlinks for nest
# TODO check existence and contents beforehand
echo "Replacing data/userfiles and data/projects/knoweng/networks with symlinks"
rm -rf data/userfiles
ln -s $NETWORK_SHARE_BASE_PATH/$NETID/userfiles data/userfiles
rm -rf data/projects/knoweng/networks
ln -s $NETWORK_SHARE_BASE_PATH/$NETID/networks data/projects/knoweng/networks

# point chronos_job.py at the analytics top-level directory
# TODO handle NETWORK_SHARE_BASE_PATH, too (but no good reason for that until
# we handle the redis and chronos settings, and by the time we tackle those,
# this may all be obsolete)
echo "Changing configuration in python code (restart nest_jobs_i afterward if it's already running)"
echo "git status will report that nest_py/knoweng/jobs/chronos_job.py has been changed; don't commit those changes"
sed -i "s/YOUR_NET_ID/$NETID/g" nest_py/knoweng/jobs/chronos_executor.py

# TODO run a simple chronos job, ideally from the nest_jobs container (to test
# docker networking), that reads something from userfiles and networks and
# writes to userfiles and logs
