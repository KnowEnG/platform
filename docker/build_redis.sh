echo "hi from build_redis.sh"
docker build --file=Dockerfile-redis --tag=knowengdev/redis:latest ..
