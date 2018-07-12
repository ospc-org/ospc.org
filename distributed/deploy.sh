mode=$1
region=us-east-2

pip install --user awscli
eval $(aws ecr get-login --region $region --no-include-email)

function tagpush() {
  docker tag opensourcepolicycenter/$1:$TAG $AWS_ACCOUNT_ID.dkr.ecr.$region.amazonaws.com/$mode-celeryflask:$1
  docker push $AWS_ACCOUNT_ID.dkr.ecr.$region.amazonaws.com/$mode-celeryflask:$1
}

tagpush flask
tagpush celery

function redeploy() {
  aws ecs update-service --cluster $mode-ecs-cluster --service $mode-$1 --region $region --force-new-deployment >/dev/null 2>&1
  echo "$1 deploy exit code: $?"
}

redeploy flask
redeploy celery
