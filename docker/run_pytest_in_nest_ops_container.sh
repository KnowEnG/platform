#runs the python test in a container that uses the nest_ops image,
# but is linked to postgres and redis containers.
#requires postgres and redis to be already running

#this script to be called from inside nest_ops, which should
#have the user and group env variables *of the host machine* set.
echo docker user_id $DOCKER_HOST_USER_ID
echo docker user_name $DOCKER_HOST_USER_NAME
echo docker group_id $DOCKER_HOST_DOCKER_GROUP_ID
echo project_dir $DOCKER_HOST_NEST_DIR

DOCKER_VERSION=`docker version --format '{{.Server.Version}}'`

docker run \
	--detach=false \
	--env="PYTHONPATH=/code_live" \
	--env=DOCKER_HOST_USER_ID=$DOCKER_HOST_USER_ID \
	--env=DOCKER_HOST_USER_NAME=$DOCKER_HOST_USER_NAME \
	--env=DOCKER_HOST_DOCKER_GROUP_ID=$DOCKER_HOST_DOCKER_GROUP_ID \
	--env=DOCKER_HOST_NEST_DIR="$DOCKER_HOST_NEST_DIR" \
	--env=DOCKER_VERSION=$DOCKER_VERSION \
	--link=redis_i:redis \
	--link=postgres_i:postres \
	--name=nest_ops_test_runner \
	--rm=true \
	--volume="$DOCKER_HOST_NEST_DIR/data/userfiles":/userfiles \
	--volume="$DOCKER_HOST_NEST_DIR":/code_live \
	nest/nest_ops:latest \
	"$@"

