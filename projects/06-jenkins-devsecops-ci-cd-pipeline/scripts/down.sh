#!/usr/bin/env bash
# Tear the lab down and remove everything this project created in Docker:
# containers, networks, named volumes (including the Docker-in-Docker data, so the tool images
# pulled inside it go too) and the images this project built or pulled.
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")/.."

# Compose needs values to parse the file, but nothing is started here.
export JENKINS_ADMIN_PASSWORD=unused SONAR_ADMIN_PASSWORD=unused SONAR_DB_PASSWORD=unused SONAR_TOKEN=unused

docker compose down --volumes --rmi all --remove-orphans

# Two images were used only as build inputs for the Jenkins image, so --rmi does not cover them.
for image in jenkins/jenkins:2.568.3-lts-jdk21 docker:29.8.1-cli; do
  docker image rm "$image" >/dev/null 2>&1 && echo "removed image $image" || true
done

# BuildKit keeps layer cache outside containers, images and volumes. It is only cache, so it is cleared too.
# This clears ALL BuildKit cache on this Docker daemon; set PRUNE_BUILD_CACHE=0 to keep it.
if [ "${PRUNE_BUILD_CACHE:-1}" = "1" ]; then
  docker builder prune --force | tail -1
fi

echo
echo "Remaining objects labelled for this project (all should be empty):"
echo "  containers: $(docker ps -aq --filter label=com.docker.compose.project=jenkins-devsecops | wc -l | tr -d ' ')"
echo "  volumes:    $(docker volume ls -q --filter label=com.docker.compose.project=jenkins-devsecops | wc -l | tr -d ' ')"
echo "  networks:   $(docker network ls -q --filter label=com.docker.compose.project=jenkins-devsecops | wc -l | tr -d ' ')"
