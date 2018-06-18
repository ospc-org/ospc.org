#!/usr/bin/env bash

docker tag opensourcepolicycenter/distributed:$OLDTAG opensourcepolicycenter/distributed:$NEWTAG
docker tag opensourcepolicycenter/flask:$OLDTAG opensourcepolicycenter/flask:$NEWTAG
docker tag opensourcepolicycenter/celery:$OLDTAG opensourcepolicycenter/celery:$NEWTAG

docker push opensourcepolicycenter/distributed:$NEWTAG
docker push opensourcepolicycenter/flask:$NEWTAG
docker push opensourcepolicycenter/celery:$NEWTAG
