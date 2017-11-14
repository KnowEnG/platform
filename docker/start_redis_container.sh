#this script to be called from inside nest_ops, which should
#have the user and group env variables *of the host machine* set.
echo docker user $DOCKER_HOST_USER_ID
echo docker group $DOCKER_HOST_DOCKER_GROUP_ID
docker run \
	--detach=true \
	--name=redis_i \
	knowengdev/redis:latest \
	"$@"
	#--user=$DOCKER_HOST_USER_ID:$DOCKER_HOST_DOCKER_GROUP_ID \

#FIXME: can't set the user b/c it tries and fails to chown '.'
# where does the data file go on the docker host machine?
# should it be a mounted volume?

