#this will clean out the docker cache of images
#
#note: this script should NOT depend on nest_ops, as it
#does maintenance on the docker installation on the current machine.
#
#jenkins runs this nightly to free up disk space.

#https://meta.discourse.org/t/low-on-disk-space-cleaning-up-old-docker-containers/15792/2
docker rm -f `docker ps -a | grep Exited | awk '{print $1 }'`
docker rmi -f `docker images -aq`
