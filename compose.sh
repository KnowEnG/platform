#!/bin/bash
git rev-parse HEAD > .git-sha
docker run -it --rm --privileged -v $HOME/.docker:/root/.docker -v /var/run/docker.sock:/var/run/docker.sock -v $(pwd):/workdir -w /workdir docker/compose:1.15.0 "$@"
