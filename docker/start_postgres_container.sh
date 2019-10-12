#this script to be called from inside nest_ops, which should
#have the user and group env variables *of the host machine* set.
echo docker user $DOCKER_HOST_USER_ID
echo docker group $DOCKER_HOST_DOCKER_GROUP_ID
echo project_dir $DOCKER_HOST_NEST_DIR

docker run \
	--name=postgres_i \
	--publish=5432:5432 \
	--detach=true \
	--env=PGDATA="/data/db/postgres" \
	--env=POSTGRES_USER="nest" \
	--env=POSTGRES_PASSWORD="Toaslej8" \
	--volume="$DOCKER_HOST_NEST_DIR/data/db":/data/db \
	nest/postgres:latest 
