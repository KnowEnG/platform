echo "hi from build_redis.sh"
docker build --file=Dockerfile-redis --tag=nest/redis:latest ..
