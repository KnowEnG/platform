#run as the current user in group 'docker to
#make all generated files owned by user:docker and
#can access the docker daemon b/c in group docker
USER_ID=`id -u`
USER_NAME=`id -un`
DOCKER_GROUP_ID=`getent group docker |cut -d ':' -f 3`
DOCKER_PROJECT_DIR="$(cd -P -- "$(dirname -- "$0")" && pwd -P)"
PROJECT_DIR=$DOCKER_PROJECT_DIR/../
if [ -t 1 ] ; then tty=true; else tty=false; fi
DOCKER_VERSION=`docker version --format '{{.Server.Version}}'`
#give the container a unique name so that mutliple nest_ops commands
#can happen at the same time (or nest_ops can call itself)
RANDO_CONTAINER_NAME=nest_ops_$(uuidgen |head -c 5)
HOST_USER_SSH_DIR=~/.ssh
# note we include /networks volume below because it's often
# a symlink on the host, so the /code_live volume won't capture its contents
# TODO: run seed job from nest_jobs, which already has a knoweng-specific start
# script, and remove the knoweng-specific volume here
docker run \
	--env=DOCKER_HOST_USER_ID=$USER_ID \
	--env=DOCKER_HOST_USER_NAME=$USER_NAME \
	--env=DOCKER_HOST_DOCKER_GROUP_ID=$DOCKER_GROUP_ID \
	--env=DOCKER_HOST_NEST_DIR="$PROJECT_DIR" \
	--env=DOCKER_VERSION=$DOCKER_VERSION \
	--interactive=true \
    --privileged=true \
	--name=$RANDO_CONTAINER_NAME \
	--rm=true \
	--tty=$tty \
	--volume=$HOST_USER_SSH_DIR/id_rsa:/ssh/id_rsa \
	--volume="$PROJECT_DIR:/code_live" \
	--volume="$PROJECT_DIR/data/projects/knoweng/networks:/networks" \
	--volume=/var/run/docker.sock:/var/run/docker.sock \
    --volume=/usr/bin/docker:/usr/bin/docker \
	--volume="$DOCKER_PROJECT_DIR/nest_ops_ssh_config":/ssh/config \
	--workdir=/code_live/ \
	nest/nest_ops:latest \
	"$@"
