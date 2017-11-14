#script to perform build and tests on a feature branch

CI_SCRIPT_DIR=`dirname $0`
PROJECT_ROOT_DIR=$CI_SCRIPT_DIR/../

#stop any containers running from previous run. Getting an
#Error message that they aren't found is the common case, so filter those messages
docker stop nest_ops_i redis_i nest_jobs_i nest_flask_i postgres_i 2>&1 | grep -v "no such id" | grep -v "failed to stop"
docker rm nest_ops_i redis_i nest_jobs_i nest_flask_i postgres_i 2>&1 | grep -v "no such id" |grep -v "failed to remove"

cd $PROJECT_ROOT_DIR/docker &&
sh build_nest_ops.sh &&
cd .. &&
./nest_ops ci feature

