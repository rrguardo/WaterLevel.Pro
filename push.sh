#!/bin/bash

set -e

cd ~/wlp/
git pull
docker compose -f docker/docker-compose.yml up -d --build
