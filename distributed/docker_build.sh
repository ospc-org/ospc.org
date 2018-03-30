#!/bin/bash

TAG=v1.5.0.1

echo 'building images...'
docker build --no-cache -t opensourcepolicycenter/distributed:$TAG ./ --build-arg PUF_TOKEN=$(cat ~/.ospc_anaconda_token)
docker build --no-cache -t opensourcepolicycenter/flask:$TAG --file Dockerfile.flask ./
docker build --no-cache -t opensourcepolicycenter/celery:$TAG --file Dockerfile.celery ./

echo 'pushing images...'
docker push opensourcepolicycenter/distributed:$TAG
docker push opensourcepolicycenter/flask:$TAG
docker push opensourcepolicycenter/celery:$TAG
