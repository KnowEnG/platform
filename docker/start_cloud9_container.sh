# 1. make sure your id_rsa file is found in ~/.ssh (you might want to protect
#    it with a passphrase, because anyone who logs in to the IDE will be have
#    access to the file)
# 2. set environment variables for your IDE user name and password:
#        export CLOUD9_USERNAME=<the user name you want to use for the IDE>
#        export CLOUD9_PASSWORD=<the password you want to use for the IDE>
# 3. run this script
# 4. visit http://<your host name>:8001/ to load the IDE
# 5. in the IDE's command prompt tab, you'll want to ssh back to your host
#    instead of running commands inside the IDE container:
#        ssh -i /workspace/.ssh/id_rsa <your user name on the host>@<your host name>
if [ -z "$CLOUD9_USERNAME" ]; then 
    echo "ERROR: you must set the CLOUD9_USERNAME environment variable"
    exit 1
fi
if [ -z "$CLOUD9_PASSWORD" ]; then 
    echo "ERROR: you must set the CLOUD9_PASSWORD environment variable"
    exit 1
fi
# Uncomment if running as ubuntu
#HOME_DIR="$HOME"

# Uncomment if running as root
HOME_DIR="/home/ubuntu"
docker run \
    --name cloud9 \
    -d \
    -v $HOME_DIR:/cloud9/workspace \
    -v $HOME_DIR:/workspace \
    --env=C9_EXTRA="--collab --auth $CLOUD9_USERNAME:$CLOUD9_PASSWORD" \
    -p 8001:8080 \
    eeacms/cloud9
