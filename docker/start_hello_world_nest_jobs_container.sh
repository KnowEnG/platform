#this script to be called from inside nest_ops, which should
#have the user and group env variables *of the host machine* set.
echo docker user $DOCKER_HOST_USER_ID
echo docker group $DOCKER_HOST_DOCKER_GROUP_ID
echo project_dir $DOCKER_HOST_NEST_DIR

docker run \
    --detach=true \
    --link=redis_i:redis \
    --link=nest_flask_i:flask \
    --name=nest_jobs_i \
    --user=$DOCKER_HOST_USER_ID:$DOCKER_HOST_DOCKER_GROUP_ID \
    --volume="$DOCKER_HOST_NEST_DIR/data/userfiles":/userfiles \
    --volume="$DOCKER_HOST_NEST_DIR":/code_live \
    --env="PYTHONPATH=/code_live" \
    --env="PROJECT_ENV=hello_world" \
    knowengdev/nest_jobs:latest 
