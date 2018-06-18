#!/bin/bash

echo 'building images...'
docker build -t opensourcepolicycenter/distributed:$TAG ./ --build-arg PUF_TOKEN=$(cat ~/.ospc_anaconda_token)
docker build --build-arg TAG=$TAG -t opensourcepolicycenter/flask:$TAG --file Dockerfile.flask ./
docker build --build-arg TAG=$TAG -t opensourcepolicycenter/celery:$TAG --file Dockerfile.celery ./

echo 'pushing images...'
docker push opensourcepolicycenter/distributed:$TAG
docker push opensourcepolicycenter/flask:$TAG
docker push opensourcepolicycenter/celery:$TAG
