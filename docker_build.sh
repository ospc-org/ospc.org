#!/bin/bash

pushd distributed

echo 'building images...'
docker build -t opensourcepolicycenter/distributed:$TAG ./ --build-arg PUF_TOKEN=$(cat ~/.ospc_anaconda_token)
docker build --build-arg TAG=$TAG -t opensourcepolicycenter/flask:$TAG --file Dockerfile.flask ./
docker build --build-arg TAG=$TAG -t opensourcepolicycenter/celery:$TAG --file Dockerfile.celery ./

echo 'pushing images...'
docker push opensourcepolicycenter/distributed:$TAG
docker push opensourcepolicycenter/flask:$TAG
docker push opensourcepolicycenter/celery:$TAG

popd

echo 'building web image...'
docker build --build-arg NEW_RELIC_TOKEN=$(cat ~/newrelic-$VERSION) -t opensourcepolicycenter/web:$TAG ./

echo 'tagging and pushing web image...'
docker tag opensourcepolicycenter/web:$TAG registry.heroku.com/ospc-$VERSION/web
docker push registry.heroku.com/ospc-$VERSION/web
heroku container:release web -a ospc-$VERSION
