#this script to be called from inside nest_ops, which should
#have the user and group env variables *of the host machine* set.
echo docker user $DOCKER_HOST_USER_ID
echo docker group $DOCKER_HOST_DOCKER_GROUP_ID
echo project_dir $DOCKER_HOST_NEST_DIR
echo runlevel $NEST_RUNLEVEL

docker run \
    --detach=true \
    --link=redis_i:redis \
    --name=nest_flask_i \
    --publish=80:80 \
    --publish=443:443 \
    --volume="$DOCKER_HOST_NEST_DIR/data/userfiles":/userfiles \
    --volume="$DOCKER_HOST_NEST_DIR":/code_live \
    --volume="$DOCKER_HOST_NEST_DIR/nest_flask_etc/uwsgi":/etc/uwsgi \
    --volume="$DOCKER_HOST_NEST_DIR/nest_flask_etc/supervisor":/etc/supervisor \
    --volume="$DOCKER_HOST_NEST_DIR/nest_flask_etc/nginx":/etc/nginx \
    --env="PROJECT_ENV=hello_world" \
    --env="NEST_RUNLEVEL=$NEST_RUNLEVEL" \
	--workdir=/code_live \
    knowengdev/nest_flask:latest 

